#!/usr/bin/env python3
"""
Healthcheck-Script für Agent-Container
Prüft Verbindung zu Ollama auf GMKTec evo x2
"""

import os
import sys
import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

async def check_ollama():
    """Check if Ollama is reachable"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{OLLAMA_BASE_URL}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m.get('name') for m in data.get('models', [])]
                    logger.info(f"Ollama reachable at {OLLAMA_BASE_URL}")
                    logger.info(f"Available models: {models}")
                    
                    # Check if configured model is available
                    if OLLAMA_MODEL in models:
                        logger.info(f"✅ Configured model '{OLLAMA_MODEL}' is available")
                        return 0
                    else:
                        logger.warning(f"⚠️ Configured model '{OLLAMA_MODEL}' not found. Available: {models}")
                        return 0  # Still healthy, just wrong model
                else:
                    logger.error(f"Ollama returned status {response.status}")
                    return 1
    except aiohttp.ClientConnectorError as e:
        logger.error(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}: {e}")
        return 1
    except asyncio.TimeoutError:
        logger.error(f"Timeout connecting to Ollama at {OLLAMA_BASE_URL}")
        return 1
    except Exception as e:
        logger.error(f"Error checking Ollama: {e}")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(check_ollama())
    sys.exit(exit_code)

