"""
Autogen Agent Network for Travel Expense Report Review
Implements specialized agents: Chat Agent, Document Agent, Accounting Agent
"""

import os
import json
import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import base64
from collections import deque

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Memory configuration - große Gedächtnisgröße für jeden Agenten
MEMORY_MAX_ENTRIES = int(os.getenv('AGENT_MEMORY_MAX_ENTRIES', '10000'))  # 10000 Einträge pro Agent
MEMORY_SUMMARY_INTERVAL = int(os.getenv('AGENT_MEMORY_SUMMARY_INTERVAL', '100'))  # Zusammenfassung alle 100 Einträge

# Ollama configuration
# For Proxmox deployment: LLMs run on GMKTec evo x2 in local network
# Default: http://localhost:11434 (local)
# Network: http://GMKTEC_IP:11434 (e.g. http://192.168.178.155:11434)
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'Qwen2.5:32B')
OLLAMA_MODEL_CHAT = os.getenv('OLLAMA_MODEL_CHAT', OLLAMA_MODEL)
OLLAMA_MODEL_DOCUMENT = os.getenv('OLLAMA_MODEL_DOCUMENT', OLLAMA_MODEL)
OLLAMA_MODEL_ACCOUNTING = os.getenv('OLLAMA_MODEL_ACCOUNTING', OLLAMA_MODEL)
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '300'))  # 5 minutes default
OLLAMA_MAX_RETRIES = int(os.getenv('OLLAMA_MAX_RETRIES', '3'))
OLLAMA_RETRY_DELAY = float(os.getenv('OLLAMA_RETRY_DELAY', '2.0'))  # seconds

# Prompt directory
PROMPTS_DIR = Path(__file__).parent / "prompts"

class AgentMemoryEntry(BaseModel):
    """Einzelner Memory-Eintrag für einen Agenten"""
    entry_id: str
    agent_name: str
    entry_type: str  # "conversation", "analysis", "decision", "pattern", "insight", "error", "correction"
    content: str  # Der eigentliche Inhalt
    context: Optional[Dict[str, Any]] = None  # Zusätzlicher Kontext
    metadata: Optional[Dict[str, Any]] = None  # Metadaten (z.B. confidence, source, etc.)
    timestamp: datetime
    tags: List[str] = []  # Tags für bessere Suche

class AgentMemory:
    """
    Großes persistentes Gedächtnis für Agenten
    Speichert Konversationen, Erkenntnisse, Muster und historische Entscheidungen
    """
    
    def __init__(self, agent_name: str, db=None):
        self.agent_name = agent_name
        self.db = db
        self.collection_name = "agent_memory"
        self._cache: deque = deque(maxlen=500)  # In-Memory Cache für schnellen Zugriff
        self._cache_loaded = False
    
    async def initialize(self):
        """Initialisiere Memory und lade Cache"""
        if self.db and not self._cache_loaded:
            try:
                # Lade die letzten 500 Einträge in den Cache
                async for entry in self.db[self.collection_name].find(
                    {"agent_name": self.agent_name}
                ).sort("timestamp", -1).limit(500):
                    self._cache.appendleft(entry)
                self._cache_loaded = True
                logger.info(f"AgentMemory für {self.agent_name} initialisiert: {len(self._cache)} Einträge geladen")
            except Exception as e:
                logger.warning(f"Fehler beim Laden des Memory-Cache für {self.agent_name}: {e}")
                self._cache_loaded = True  # Setze auf True, um weitere Versuche zu vermeiden
    
    async def add(self, 
                  entry_type: str, 
                  content: str, 
                  context: Optional[Dict[str, Any]] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  tags: Optional[List[str]] = None) -> str:
        """Füge einen neuen Memory-Eintrag hinzu"""
        entry_id = str(uuid.uuid4())
        entry = {
            "entry_id": entry_id,
            "agent_name": self.agent_name,
            "entry_type": entry_type,
            "content": content,
            "context": context or {},
            "metadata": metadata or {},
            "timestamp": datetime.utcnow(),
            "tags": tags or []
        }
        
        # Füge zum Cache hinzu
        self._cache.append(entry)
        
        # Persistiere in Datenbank
        if self.db:
            try:
                await self.db[self.collection_name].insert_one(entry)
                
                # Prüfe, ob Zusammenfassung nötig ist
                count = await self.db[self.collection_name].count_documents({"agent_name": self.agent_name})
                if count > 0 and count % MEMORY_SUMMARY_INTERVAL == 0:
                    await self._create_summary()
                    
            except Exception as e:
                logger.error(f"Fehler beim Speichern des Memory-Eintrags für {self.agent_name}: {e}")
        
        return entry_id
    
    async def search(self, 
                    query: Optional[str] = None,
                    entry_type: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    limit: int = 50,
                    days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Suche in Memory-Einträgen"""
        results = []
        
        if self.db:
            try:
                # Baue Query auf
                db_query = {"agent_name": self.agent_name}
                
                if entry_type:
                    db_query["entry_type"] = entry_type
                
                if tags:
                    db_query["tags"] = {"$in": tags}
                
                if days:
                    cutoff_date = datetime.utcnow() - timedelta(days=days)
                    db_query["timestamp"] = {"$gte": cutoff_date}
                
                # Suche in Datenbank
                async for entry in self.db[self.collection_name].find(db_query).sort("timestamp", -1).limit(limit):
                    results.append(entry)
                
                # Wenn Text-Suche, filtere nach Inhalt
                if query and query.strip():
                    query_lower = query.lower()
                    results = [
                        entry for entry in results
                        if query_lower in entry.get("content", "").lower() or
                           query_lower in str(entry.get("context", {})).lower()
                    ]
                    
            except Exception as e:
                logger.error(f"Fehler beim Suchen im Memory für {self.agent_name}: {e}")
        else:
            # Fallback: Suche nur im Cache
            for entry in self._cache:
                if entry_type and entry.get("entry_type") != entry_type:
                    continue
                if tags and not any(tag in entry.get("tags", []) for tag in tags):
                    continue
                if query and query.lower() not in entry.get("content", "").lower():
                    continue
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results[:limit]
    
    async def get_recent(self, limit: int = 20, entry_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Hole die letzten Einträge"""
        return await self.search(entry_type=entry_type, limit=limit)
    
    async def get_patterns(self, pattern_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Hole gespeicherte Muster und Erkenntnisse"""
        return await self.search(entry_type="pattern", limit=100)
    
    async def get_insights(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Hole gespeicherte Erkenntnisse"""
        return await self.search(entry_type="insight", limit=limit)
    
    async def get_context_for_prompt(self, 
                                     max_tokens: int = 2000,
                                     relevant_query: Optional[str] = None) -> str:
        """
        Generiere Kontext für LLM-Prompt aus Memory
        Kombiniert relevante Einträge und Erkenntnisse
        """
        context_parts = []
        
        # Hole relevante Erkenntnisse und Muster
        insights = await self.get_insights(limit=10)
        patterns = await self.get_patterns()
        
        if insights:
            context_parts.append("=== Gelernte Erkenntnisse ===")
            for insight in insights[:5]:  # Top 5 Erkenntnisse
                context_parts.append(f"- {insight.get('content', '')}")
                if insight.get('timestamp'):
                    context_parts.append(f"  (Gespeichert: {insight['timestamp']})")
        
        if patterns:
            context_parts.append("\n=== Gelernte Muster ===")
            for pattern in patterns[:5]:  # Top 5 Muster
                context_parts.append(f"- {pattern.get('content', '')}")
        
        # Wenn relevante Query, hole passende Einträge
        if relevant_query:
            relevant = await self.search(query=relevant_query, limit=10)
            if relevant:
                context_parts.append(f"\n=== Relevante historische Kontexte ===")
                for entry in relevant[:5]:
                    context_parts.append(f"- [{entry.get('entry_type', 'unknown')}] {entry.get('content', '')[:200]}")
                    if entry.get('timestamp'):
                        context_parts.append(f"  (Von: {entry['timestamp']})")
        
        # Hole die letzten wichtigen Entscheidungen
        recent_decisions = await self.search(entry_type="decision", limit=5)
        if recent_decisions:
            context_parts.append("\n=== Letzte wichtige Entscheidungen ===")
            for decision in recent_decisions:
                context_parts.append(f"- {decision.get('content', '')[:300]}")
        
        context = "\n".join(context_parts)
        
        # Kürze auf max_tokens (ungefähre Zeichenanzahl)
        if len(context) > max_tokens * 4:  # ~4 Zeichen pro Token
            context = context[:max_tokens * 4] + "\n... (weitere Einträge im Memory verfügbar)"
        
        return context
    
    async def _create_summary(self):
        """Erstelle eine Zusammenfassung von Memory-Einträgen (für große Memories)"""
        # Diese Funktion kann periodisch aufgerufen werden, um das Memory zu komprimieren
        # Für jetzt nur Logging
        count = await self.db[self.collection_name].count_documents({"agent_name": self.agent_name})
        logger.info(f"AgentMemory für {self.agent_name}: {count} Einträge gespeichert (Zusammenfassung könnte nützlich sein)")
    
    async def add_conversation(self, user_message: str, agent_response: str, context: Optional[Dict] = None):
        """Speichere eine Konversation"""
        content = f"User: {user_message}\nAgent: {agent_response}"
        await self.add("conversation", content, context=context, tags=["conversation", "interaction"])
    
    async def add_analysis(self, analysis_result: str, metadata: Optional[Dict] = None):
        """Speichere ein Analyseergebnis"""
        await self.add("analysis", analysis_result, metadata=metadata, tags=["analysis", "document"])
    
    async def add_decision(self, decision: str, confidence: float = 1.0, context: Optional[Dict] = None):
        """Speichere eine getroffene Entscheidung"""
        await self.add("decision", decision, 
                      metadata={"confidence": confidence}, 
                      context=context,
                      tags=["decision"])
    
    async def add_pattern(self, pattern: str, examples: Optional[List[str]] = None):
        """Speichere ein gelerntes Muster"""
        context = {"examples": examples} if examples else {}
        await self.add("pattern", pattern, context=context, tags=["pattern", "learning"])
    
    async def add_insight(self, insight: str, source: Optional[str] = None):
        """Speichere eine Erkenntnis"""
        metadata = {"source": source} if source else {}
        await self.add("insight", insight, metadata=metadata, tags=["insight", "learning"])
    
    async def add_correction(self, original: str, corrected: str, reason: str):
        """Speichere eine Korrektur"""
        content = f"Original: {original}\nKorrigiert: {corrected}\nGrund: {reason}"
        await self.add("correction", content, tags=["correction", "learning"])

class AgentMessageBus:
    """Message bus for inter-agent communication"""
    
    def __init__(self):
        self.messages: deque = deque(maxlen=1000)  # Keep last 1000 messages
        self.subscribers: Dict[str, List[callable]] = {}
    
    def subscribe(self, agent_name: str, callback: callable):
        """Subscribe an agent to messages"""
        if agent_name not in self.subscribers:
            self.subscribers[agent_name] = []
        self.subscribers[agent_name].append(callback)
    
    def publish(self, from_agent: str, to_agent: str, message: Dict[str, Any]):
        """Publish a message from one agent to another"""
        msg = {
            "from": from_agent,
            "to": to_agent,
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.messages.append(msg)
        
        # Notify subscribers
        if to_agent in self.subscribers:
            for callback in self.subscribers[to_agent]:
                try:
                    callback(msg)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")
    
    def broadcast(self, from_agent: str, message: Dict[str, Any]):
        """Broadcast message to all agents"""
        for agent_name in self.subscribers.keys():
            if agent_name != from_agent:
                self.publish(from_agent, agent_name, message)
    
    def get_messages(self, agent_name: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get messages for a specific agent or all messages"""
        if agent_name:
            return [msg for msg in self.messages if msg.get("to") == agent_name][-limit:]
        return list(self.messages)[-limit:]

def load_prompt(prompt_file: str) -> str:
    """Load prompt from markdown file"""
    prompt_path = PROMPTS_DIR / prompt_file
    if not prompt_path.exists():
        logger.warning(f"Prompt file not found: {prompt_path}, using default")
        return ""
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Remove markdown header if present
            if content.startswith('# '):
                lines = content.split('\n')
                # Skip until we find the actual prompt content
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('#'):
                        return '\n'.join(lines[i:]).strip()
            return content.strip()
    except Exception as e:
        logger.error(f"Error loading prompt from {prompt_path}: {e}")
        return ""

# Spesensätze API (Beispiel - würde durch echte API ersetzt)
# Quelle: Bundesfinanzministerium Verpflegungsmehraufwand
MEAL_ALLOWANCE_RATES = {
    "DE": {"24h": 28.0, "abwesend": 14.0},  # Deutschland in Euro
    "AT": {"24h": 41.00, "abwesend": 20.50},  # Österreich
    "CH": {"24h": 70.00, "abwesend": 35.00},  # Schweiz
    "FR": {"24h": 57.00, "abwesend": 28.50},  # Frankreich
    "IT": {"24h": 57.00, "abwesend": 28.50},  # Italien
    "ES": {"24h": 58.50, "abwesend": 29.25},  # Spanien
    "GB": {"24h": 52.00, "abwesend": 26.00},  # Großbritannien
    "US": {"24h": 89.00, "abwesend": 44.50},  # USA
    "DEFAULT": {"24h": 28.0, "abwesend": 14.0}  # Default: Deutschland
}

class AgentMessage(BaseModel):
    """Message between agents or agent and user"""
    sender: str  # agent name or "user"
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

class DocumentAnalysis(BaseModel):
    """Result of document analysis"""
    document_type: str  # e.g. "hotel_receipt", "restaurant_bill", "toll_receipt", "parking", "fuel", "train_ticket"
    language: str  # detected language
    translated_content: Optional[str] = None  # if translation needed
    extracted_data: Dict[str, Any]  # extracted fields
    validation_issues: List[str] = []  # issues found
    completeness_check: Dict[str, bool] = {}  # e.g. {"has_tax_number": True, "has_company_address": False}
    confidence: float  # 0.0 to 1.0

class ExpenseAssignment(BaseModel):
    """Expense assignment to travel entry"""
    receipt_id: str
    entry_date: str  # YYYY-MM-DD
    category: str  # "hotel", "meals", "tolls", "parking", "fuel", "transport", "other"
    amount: float
    currency: str = "EUR"
    meal_allowance_added: Optional[float] = None  # if Verpflegungsmehraufwand was added
    assignment_confidence: float

class AgentResponse(BaseModel):
    """Response from an agent"""
    agent_name: str
    message: str
    action_taken: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    requires_user_input: bool = False
    next_agent: Optional[str] = None

# ============================================================================
# Agent Tools System - Web-Zugriff und externe APIs
# ============================================================================

class AgentTool(BaseModel):
    """Basis-Klasse für Agent-Tools"""
    name: str
    description: str
    parameters: Dict[str, Any]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Führe das Tool aus - muss von Unterklassen implementiert werden"""
        raise NotImplementedError("Subclasses must implement execute()")

class WebSearchTool(AgentTool):
    """Tool für Web-Suche - holt aktuelle Informationen aus dem Internet"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Suche nach aktuellen Informationen im Internet. Nützlich für aktuelle Daten, Spesensätze, Währungsinformationen, etc.",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Suchanfrage (z.B. 'aktuelle Verpflegungsmehraufwand Sätze 2025 Deutschland')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximale Anzahl an Ergebnissen (Standard: 5)",
                    "default": 5
                }
            }
        )
        self._session = None
    
    async def _get_session(self):
        """Get aiohttp session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session
    
    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Führe Web-Suche aus"""
        try:
            # Verwende DuckDuckGo HTML-Suche (kein API-Key nötig)
            # Alternative: Man könnte auch eine echte Search API verwenden (Google, Bing, etc.)
            search_url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            
            session = await self._get_session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with session.get(search_url, params=params, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    # Einfache Text-Extraktion aus HTML (vereinfacht)
                    # In Produktion würde man BeautifulSoup verwenden
                    import re
                    # Extrahiere Snippets aus dem HTML
                    snippets = re.findall(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
                    results = []
                    for i, snippet in enumerate(snippets[:max_results]):
                        # HTML-Tags entfernen
                        clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                        if clean_snippet:
                            results.append({
                                "title": clean_snippet[:100],
                                "snippet": clean_snippet[:300]
                            })
                    
                    return {
                        "success": True,
                        "query": query,
                        "results": results,
                        "count": len(results)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "query": query
                    }
                    
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

class CurrencyExchangeTool(AgentTool):
    """Tool für Währungswechselkurse - holt aktuelle Wechselkurse"""
    
    def __init__(self):
        super().__init__(
            name="currency_exchange",
            description="Holt aktuelle Wechselkurse zwischen verschiedenen Währungen. Nützlich für Reisekostenabrechnungen in Fremdwährung.",
            parameters={
                "from_currency": {
                    "type": "string",
                    "description": "Quell-Währung (z.B. 'USD', 'EUR', 'GBP')"
                },
                "to_currency": {
                    "type": "string",
                    "description": "Ziel-Währung (Standard: 'EUR')",
                    "default": "EUR"
                },
                "amount": {
                    "type": "number",
                    "description": "Betrag zum Umrechnen (optional)",
                    "default": 1.0
                }
            }
        )
        self._session = None
        self._cache: Dict[str, tuple] = {}  # Cache für 1 Stunde
        self._cache_ttl = 3600  # 1 Stunde in Sekunden
    
    async def _get_session(self):
        """Get aiohttp session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session
    
    async def execute(self, from_currency: str, to_currency: str = "EUR", amount: float = 1.0) -> Dict[str, Any]:
        """Holt Wechselkurs und rechnet Betrag um"""
        try:
            from_upper = from_currency.upper()
            to_upper = to_currency.upper()
            
            if from_upper == to_upper:
                return {
                    "success": True,
                    "from_currency": from_upper,
                    "to_currency": to_upper,
                    "rate": 1.0,
                    "amount": amount,
                    "converted_amount": amount
                }
            
            # Prüfe Cache
            cache_key = f"{from_upper}_{to_upper}"
            now = datetime.utcnow().timestamp()
            if cache_key in self._cache:
                cached_rate, cached_time = self._cache[cache_key]
                if now - cached_time < self._cache_ttl:
                    converted = amount * cached_rate
                    return {
                        "success": True,
                        "from_currency": from_upper,
                        "to_currency": to_upper,
                        "rate": cached_rate,
                        "amount": amount,
                        "converted_amount": round(converted, 2),
                        "cached": True
                    }
            
            # Hole aktuellen Kurs von exchangerate-api.com (kostenlos, kein API-Key nötig)
            session = await self._get_session()
            url = f"https://api.exchangerate-api.com/v4/latest/{from_upper}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = data.get("rates", {})
                    
                    if to_upper in rates:
                        rate = rates[to_upper]
                        # Update Cache
                        self._cache[cache_key] = (rate, now)
                        
                        converted = amount * rate
                        return {
                            "success": True,
                            "from_currency": from_upper,
                            "to_currency": to_upper,
                            "rate": rate,
                            "amount": amount,
                            "converted_amount": round(converted, 2),
                            "date": data.get("date", ""),
                            "cached": False
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Währung {to_upper} nicht gefunden",
                            "from_currency": from_upper,
                            "to_currency": to_upper
                        }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "from_currency": from_upper,
                        "to_currency": to_upper
                    }
                    
        except Exception as e:
            logger.error(f"Currency exchange error: {e}")
            return {
                "success": False,
                "error": str(e),
                "from_currency": from_currency,
                "to_currency": to_currency
            }

class MealAllowanceLookupTool(AgentTool):
    """Tool für aktuelle Verpflegungsmehraufwand-Spesensätze"""
    
    def __init__(self):
        super().__init__(
            name="meal_allowance_lookup",
            description="Sucht nach aktuellen Verpflegungsmehraufwand-Spesensätzen für verschiedene Länder. Nutzt Web-Suche für aktuelle Daten.",
            parameters={
                "country": {
                    "type": "string",
                    "description": "Land oder Ländercode (z.B. 'Deutschland', 'DE', 'USA', 'US')"
                },
                "year": {
                    "type": "integer",
                    "description": "Jahr für die Spesensätze (Standard: aktuelles Jahr)",
                    "default": None
                }
            }
        )
        self.web_search = WebSearchTool()
    
    async def execute(self, country: str, year: Optional[int] = None) -> Dict[str, Any]:
        """Sucht nach aktuellen Spesensätzen"""
        try:
            if year is None:
                year = datetime.now().year
            
            # Baue Suchanfrage
            query = f"Verpflegungsmehraufwand {country} {year} Spesensätze Bundesfinanzministerium"
            
            # Nutze Web-Search-Tool
            search_result = await self.web_search.execute(query, max_results=3)
            
            if search_result.get("success") and search_result.get("results"):
                # Extrahiere Zahlen aus den Ergebnissen
                results_text = " ".join([r.get("snippet", "") for r in search_result["results"]])
                
                # Versuche Beträge zu extrahieren (vereinfacht)
                import re
                # Suche nach Euro-Beträgen wie "28,00 EUR" oder "28.00 Euro"
                amounts = re.findall(r'(\d+[.,]\d{2})\s*(?:EUR|Euro|€)', results_text, re.IGNORECASE)
                
                if amounts:
                    # Konvertiere zu float
                    try:
                        rates = [float(a.replace(",", ".")) for a in amounts[:2]]  # Nimm erste 2
                        return {
                            "success": True,
                            "country": country,
                            "year": year,
                            "rates": rates,
                            "source": "web_search",
                            "search_results": search_result["results"][:2]
                        }
                    except ValueError:
                        pass
                
                return {
                    "success": True,
                    "country": country,
                    "year": year,
                    "found_information": True,
                    "search_results": search_result["results"],
                    "note": "Spesensätze gefunden, aber Beträge müssen manuell extrahiert werden"
                }
            else:
                # Fallback auf lokale Datenbank
                country_upper = country.upper()
                if country_upper in MEAL_ALLOWANCE_RATES:
                    rates = MEAL_ALLOWANCE_RATES[country_upper]
                    return {
                        "success": True,
                        "country": country,
                        "year": year,
                        "rates": rates,
                        "source": "local_database",
                        "note": "Verwendet lokale Datenbank (möglicherweise nicht aktuell)"
                    }
                
                return {
                    "success": False,
                    "error": "Keine Spesensätze gefunden",
                    "country": country,
                    "year": year
                }
                
        except Exception as e:
            logger.error(f"Meal allowance lookup error: {e}")
            return {
                "success": False,
                "error": str(e),
                "country": country
            }

class GeocodingTool(AgentTool):
    """Tool für Geocoding - bestimmt Ländercode aus Ortsangabe"""
    
    def __init__(self):
        super().__init__(
            name="geocoding",
            description="Bestimmt Ländercode aus einer Ortsangabe oder Adresse. Nützlich für automatische Ländererkennung.",
            parameters={
                "location": {
                    "type": "string",
                    "description": "Ortsangabe (z.B. 'München', 'Berlin, Deutschland', 'New York, USA')"
                }
            }
        )
        self._session = None
    
    async def _get_session(self):
        """Get aiohttp session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session
    
    async def execute(self, location: str) -> Dict[str, Any]:
        """Bestimmt Ländercode aus Ortsangabe"""
        try:
            # Verwende Nominatim (OpenStreetMap Geocoding API) - kostenlos
            session = await self._get_session()
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": location,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            headers = {
                "User-Agent": "Stundenzettel-Web-App/1.0"  # Nominatim erfordert User-Agent
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        result = data[0]
                        address = result.get("address", {})
                        country_code = address.get("country_code", "").upper()
                        country = address.get("country", "")
                        
                        return {
                            "success": True,
                            "location": location,
                            "country_code": country_code,
                            "country": country,
                            "full_address": result.get("display_name", ""),
                            "lat": float(result.get("lat", 0)),
                            "lon": float(result.get("lon", 0))
                        }
                    else:
                        return {
                            "success": False,
                            "error": "Ort nicht gefunden",
                            "location": location
                        }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "location": location
                    }
                    
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            # Fallback auf einfache String-Erkennung
            location_lower = location.lower()
            country_mapping = {
                "deutschland": "DE", "germany": "DE",
                "österreich": "AT", "austria": "AT",
                "schweiz": "CH", "switzerland": "CH",
                "frankreich": "FR", "france": "FR",
                "italien": "IT", "italy": "IT",
                "spanien": "ES", "spain": "ES",
                "großbritannien": "GB", "uk": "GB", "england": "GB",
                "usa": "US", "vereinigte staaten": "US"
            }
            for key, code in country_mapping.items():
                if key in location_lower:
                    return {
                        "success": True,
                        "location": location,
                        "country_code": code,
                        "country": key,
                        "source": "fallback_mapping"
                    }
            
            return {
                "success": False,
                "error": str(e),
                "location": location
            }
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

class AgentToolRegistry:
    """Registry für alle verfügbaren Agent-Tools"""
    
    def __init__(self):
        self.tools: Dict[str, AgentTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Registriere Standard-Tools"""
        self.register(WebSearchTool())
        self.register(CurrencyExchangeTool())
        self.register(MealAllowanceLookupTool())
        self.register(GeocodingTool())
    
    def register(self, tool: AgentTool):
        """Registriere ein neues Tool"""
        self.tools[tool.name] = tool
        logger.info(f"Tool '{tool.name}' registriert")
    
    def get_tool(self, name: str) -> Optional[AgentTool]:
        """Hole Tool nach Namen"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Liste alle verfügbaren Tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Führe ein Tool aus"""
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' nicht gefunden",
                "available_tools": list(self.tools.keys())
            }
        
        try:
            result = await tool.execute(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": name
            }
    
    async def close(self):
        """Schließe alle Tools (für Cleanup)"""
        for tool in self.tools.values():
            if hasattr(tool, 'close') and callable(tool.close):
                try:
                    await tool.close()
                except Exception as e:
                    logger.warning(f"Error closing tool {tool.name}: {e}")

# Globale Tool-Registry
_tool_registry: Optional[AgentToolRegistry] = None

def get_tool_registry() -> AgentToolRegistry:
    """Hole die globale Tool-Registry (Singleton)"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = AgentToolRegistry()
    return _tool_registry

class OllamaLLM:
    """Wrapper for Ollama LLM API
    
    Supports remote Ollama server on GMKTec evo x2 in local network.
    Handles network connectivity, timeouts, and retries for Proxmox deployment.
    """
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = OLLAMA_TIMEOUT
        self.max_retries = OLLAMA_MAX_RETRIES
        self.retry_delay = OLLAMA_RETRY_DELAY
        self._session = None
        logger.info(f"OllamaLLM initialized: {self.base_url}, model={self.model}")
    
    async def _get_session(self):
        """Get or create aiohttp session with connection pooling"""
        if self._session is None or self._session.closed:
            # Create session with connection pooling for better performance
            connector = aiohttp.TCPConnector(
                limit=10,  # Max connections
                limit_per_host=5,  # Max connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                force_close=False,  # Reuse connections
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(
                total=self.timeout,
                connect=10,  # Connection timeout
                sock_read=self.timeout  # Read timeout
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self._session
    
    async def health_check(self) -> bool:
        """Check if Ollama server is reachable"""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    logger.info(f"Ollama health check OK: {self.base_url}")
                    return True
                else:
                    logger.warning(f"Ollama health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"Ollama health check error: {e}")
            return False
    
    async def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        """Send chat messages to Ollama and get response with retry logic"""
        # Prepare messages with system prompt
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": formatted_messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 4096  # Max tokens
                        }
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("message", {}).get("content", "")
                        if content:
                            logger.debug(f"Ollama response received (attempt {attempt + 1})")
                            return content
                        else:
                            logger.warning(f"Empty response from Ollama (attempt {attempt + 1})")
                            last_error = "Empty response from LLM"
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {response.status} - {error_text[:200]}")
                        last_error = f"API error {response.status}"
                        
            except aiohttp.ClientConnectorError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"Ollama connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    
            except asyncio.TimeoutError:
                last_error = "Request timeout"
                logger.warning(f"Ollama timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Ollama error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        # All retries failed
        error_msg = f"Fehler bei Kommunikation mit LLM nach {self.max_retries} Versuchen: {last_error}"
        logger.error(error_msg)
        return error_msg
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def extract_json(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[Dict]:
        """Extract structured JSON from LLM response"""
        extraction_prompt = f"{prompt}\n\nAntworte NUR mit einem gültigen JSON-Objekt, keine zusätzlichen Erklärungen."
        response = await self.chat([{"role": "user", "content": extraction_prompt}], system_prompt)
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON from response: {response[:200]}")
            return None

class ChatAgent:
    """Agent für Dialog und Rückfragen mit Benutzer"""
    
    def __init__(self, llm: OllamaLLM, memory: Optional[AgentMemory] = None, db=None):
        self.llm = llm
        self.name = "ChatAgent"
        self.memory = memory or AgentMemory(self.name, db)
        self.system_prompt_base = """Du bist ein hilfreicher Assistent für Reisekostenabrechnungen. 
Du stellst dem Benutzer klare Fragen zu fehlenden oder unklaren Informationen in den Reisekostenabrechnungen.
Sei präzise, freundlich und auf Deutsch.
Formuliere Fragen so, dass sie mit kurzen Antworten beantwortet werden können."""
    
    async def initialize(self):
        """Initialisiere Memory"""
        await self.memory.initialize()
    
    async def process(self, context: Dict[str, Any], user_message: Optional[str] = None) -> AgentResponse:
        """Process user message or generate question based on context"""
        report_issues = context.get("issues", [])
        missing_info = context.get("missing_info", [])
        
        # Hole relevanten Memory-Kontext
        memory_context = await self.memory.get_context_for_prompt(
            max_tokens=1500,
            relevant_query=f"{missing_info} {report_issues}" if missing_info or report_issues else None
        )
        
        # Erweitere System-Prompt mit Memory
        system_prompt = self.system_prompt_base
        if memory_context:
            system_prompt += f"\n\n=== Dein Gedächtnis (frühere Erfahrungen) ===\n{memory_context}\n"
            system_prompt += "\nNutze diese Informationen aus deinem Gedächtnis, um bessere Fragen zu stellen und den Benutzer besser zu verstehen."
        
        if user_message:
            # Process user's answer
            prompt = f"""Der Benutzer hat folgende Antwort gegeben: "{user_message}"
Kontext: {json.dumps(context, indent=2, ensure_ascii=False)}
            
Bewerte die Antwort und gib an:
- Ob die Information ausreichend ist
- Ob weitere Fragen nötig sind
- Eine Zusammenfassung der erhaltenen Informationen"""
            
            response_text = await self.llm.chat([
                {"role": "user", "content": prompt}
            ], system_prompt)
            
            # Speichere Konversation im Memory
            await self.memory.add_conversation(
                user_message=user_message,
                agent_response=response_text,
                context={"report_issues": report_issues, "missing_info": missing_info}
            )
            
            # Speichere Erkenntnis, falls neue Information
            if len(missing_info) == 0:
                await self.memory.add_insight(
                    f"Benutzer hat vollständige Informationen für Reisekostenabrechnung bereitgestellt: {user_message[:200]}",
                    source="user_conversation"
                )
            
            return AgentResponse(
                agent_name=self.name,
                message=response_text,
                requires_user_input=len(missing_info) > 0,
                next_agent="DocumentAgent" if len(report_issues) > 0 else None
            )
        else:
            # Generate questions based on context
            if missing_info:
                prompt = f"""Es fehlen folgende Informationen in der Reisekostenabrechnung:
{json.dumps(missing_info, indent=2, ensure_ascii=False)}

Formuliere eine klare, freundliche Frage an den Benutzer, um die fehlende Information zu erhalten."""
                response_text = await self.llm.chat([
                    {"role": "user", "content": prompt}
                ], system_prompt)
            else:
                response_text = "Alle Informationen sind vollständig. Die Prüfung kann fortgesetzt werden."
            
            # Speichere generierte Frage
            if missing_info:
                await self.memory.add_decision(
                    f"Frage generiert für fehlende Informationen: {missing_info}",
                    confidence=0.8,
                    context={"missing_info": missing_info}
                )
            
            return AgentResponse(
                agent_name=self.name,
                message=response_text,
                requires_user_input=len(missing_info) > 0
            )

class DocumentAgent:
    """Agent für Dokumentenanalyse: Verstehen, Übersetzen, Kategorisieren, Validieren"""
    
    def __init__(self, llm: OllamaLLM, message_bus: Optional[AgentMessageBus] = None, memory: Optional[AgentMemory] = None, db=None):
        self.llm = llm
        self.name = "DocumentAgent"
        self.message_bus = message_bus
        self.memory = memory or AgentMemory(self.name, db)
        # Load prompt from markdown file
        self.system_prompt_base = load_prompt("document_agent.md")
        if not self.system_prompt_base:
            # Fallback default prompt
            self.system_prompt_base = """Du bist ein Experte für Dokumentenanalyse von Reisekostenbelegen.
Deine Aufgaben:
1. Dokumente kategorisieren (Hotel, Restaurant, Maut, Parken, Tanken, Bahnticket, etc.)
2. Sprache erkennen und bei Bedarf übersetzen
3. Relevante Daten extrahieren (Betrag, Datum, Steuernummer, Firmenanschrift, etc.)
4. Vollständigkeit prüfen (Echtheit, Steuernummer vorhanden, Firmenanschrift, etc.)
5. Probleme und Unstimmigkeiten identifizieren

Antworte präzise und strukturiert."""
        
        # Subscribe to messages from other agents
        if self.message_bus:
            self.message_bus.subscribe(self.name, self.handle_agent_message)
    
    async def initialize(self):
        """Initialisiere Memory"""
        await self.memory.initialize()
    
    def handle_agent_message(self, message: Dict):
        """Handle messages from other agents"""
        logger.info(f"DocumentAgent received message from {message.get('from')}: {message.get('content')}")
        # Can request clarification from Chat Agent if needed
        if message.get('from') == 'ChatAgent':
            # Chat Agent might request document re-analysis
            pass
    
    def extract_pdf_text(self, pdf_path: str, encryption=None) -> str:
        """
        Extract text from PDF file
        Handles encrypted files for DSGVO compliance
        """
        extracted_text = ""
        
        try:
            # Check if file is encrypted and decrypt if needed
            file_data = None
            if encryption:
                try:
                    # Try to decrypt first
                    file_data = encryption.decrypt_file(Path(pdf_path))
                    # Write decrypted data to temp file for processing
                    temp_path = Path(pdf_path).with_suffix('.tmp.pdf')
                    with open(temp_path, 'wb') as f:
                        f.write(file_data)
                    pdf_path = str(temp_path)
                except Exception:
                    # File might not be encrypted, proceed normally
                    pass
            
            if HAS_PDFPLUMBER:
                # Use pdfplumber (better for tables and structured data)
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            extracted_text += text + "\n"
            elif HAS_PYPDF2:
                # Fallback to PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            extracted_text += text + "\n"
            
            # Clean up temp file if created
            if file_data and Path(pdf_path).suffix == '.tmp.pdf':
                try:
                    Path(pdf_path).unlink()
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Could not extract text from PDF {pdf_path}: {e}")
        
        return extracted_text
    
    async def analyze_document(self, receipt_path: str, filename: str, encryption=None) -> DocumentAnalysis:
        """Analyze a PDF receipt document"""
        try:
            # Extract text from PDF (handles encryption if needed)
            pdf_text = self.extract_pdf_text(receipt_path, encryption)
            
            # Limit text length for LLM (first 5000 characters)
            pdf_text_limited = pdf_text[:5000] if pdf_text else "Kein Text extrahiert"
            
            # Hole relevanten Memory-Kontext für ähnliche Dokumente
            memory_context = await self.memory.get_context_for_prompt(
                max_tokens=1500,
                relevant_query=f"document analysis {filename} {pdf_text_limited[:200]}"
            )
            
            # Erweitere System-Prompt mit Memory
            system_prompt = self.system_prompt_base
            if memory_context:
                system_prompt += f"\n\n=== Dein Gedächtnis (frühere Dokumentenanalysen) ===\n{memory_context}\n"
                system_prompt += "\nNutze diese Erfahrungen aus deinem Gedächtnis, um ähnliche Dokumente besser zu analysieren und bekannte Muster zu erkennen."
            
            prompt = f"""Analysiere das folgende Reisekosten-Dokument:

Dateiname: {filename}
Extrahierter Text aus PDF:
{pdf_text_limited}

Analysiere und extrahiere folgende Informationen:
1. Dokumenttyp: hotel_receipt, restaurant_bill, toll_receipt, parking, fuel, train_ticket, other
2. Sprache des Dokuments
3. Betrag (Hauptbetrag)
4. Datum
5. Währung
6. Steuernummer/USt-IdNr (falls vorhanden)
7. Firmenanschrift/Kontaktdaten (falls vorhanden)
8. Vollständigkeitsprüfung:
   - Steuernummer vorhanden?
   - Firmenanschrift vorhanden?
   - Betrag klar erkennbar?
   - Datum vorhanden?
9. Probleme/Unstimmigkeiten (z.B. unleserlich, unvollständig, verdächtig)

Antworte im JSON-Format mit folgenden Feldern:
{{
  "document_type": "...",
  "language": "...",
  "extracted_data": {{
    "amount": 0.0,
    "currency": "EUR",
    "date": "YYYY-MM-DD",
    "tax_number": "...",
    "company_address": "..."
  }},
  "validation_issues": ["..."],
  "completeness_check": {{
    "has_tax_number": true/false,
    "has_company_address": true/false,
    "has_amount": true/false,
    "has_date": true/false
  }},
  "confidence": 0.0-1.0
}}"""
            
            analysis_json = await self.llm.extract_json(prompt, system_prompt)
            
            if not analysis_json:
                # Fallback: Try to extract basic info from filename
                filename_lower = filename.lower()
                doc_type = "other"
                if "hotel" in filename_lower or "unterkunft" in filename_lower:
                    doc_type = "hotel_receipt"
                elif "restaurant" in filename_lower or "essen" in filename_lower:
                    doc_type = "restaurant_bill"
                elif "maut" in filename_lower or "toll" in filename_lower:
                    doc_type = "toll_receipt"
                elif "park" in filename_lower:
                    doc_type = "parking"
                elif "tank" in filename_lower or "fuel" in filename_lower or "benzin" in filename_lower:
                    doc_type = "fuel"
                elif "bahn" in filename_lower or "train" in filename_lower or "zug" in filename_lower:
                    doc_type = "train_ticket"
                
                return DocumentAnalysis(
                    document_type=doc_type,
                    language="de",
                    extracted_data={"filename": filename},
                    validation_issues=["Konnte Dokument nicht vollständig analysieren - nur Dateiname verwendet"],
                    completeness_check={"has_tax_number": False, "has_company_address": False, "has_amount": False, "has_date": False},
                    confidence=0.3
                )
            
            # Map to DocumentAnalysis model
            analysis = DocumentAnalysis(
                document_type=analysis_json.get("document_type", "unknown"),
                language=analysis_json.get("language", "de"),
                translated_content=analysis_json.get("translated_content"),
                extracted_data=analysis_json.get("extracted_data", {}),
                validation_issues=analysis_json.get("validation_issues", []),
                completeness_check=analysis_json.get("completeness_check", {}),
                confidence=float(analysis_json.get("confidence", 0.5))
            )
            
            # Speichere Analyse im Memory
            analysis_summary = f"Dokument: {filename}, Typ: {analysis.document_type}, Betrag: {analysis.extracted_data.get('amount', 0.0)} {analysis.extracted_data.get('currency', 'EUR')}, Sprache: {analysis.language}, Konfidenz: {analysis.confidence:.2f}"
            await self.memory.add_analysis(
                analysis_summary,
                metadata={
                    "document_type": analysis.document_type,
                    "filename": filename,
                    "confidence": analysis.confidence,
                    "validation_issues_count": len(analysis.validation_issues)
                }
            )
            
            # Speichere Muster, wenn hohe Konfidenz
            if analysis.confidence > 0.8:
                pattern = f"Dokumenttyp '{analysis.document_type}' mit typischen Merkmalen: Sprache={analysis.language}, Betrag-Format={analysis.extracted_data.get('amount')}"
                await self.memory.add_pattern(pattern, examples=[filename])
            
            # Speichere Erkenntnis bei Problemen
            if analysis.validation_issues:
                insight = f"Dokument '{filename}' hat Probleme: {', '.join(analysis.validation_issues[:3])}"
                await self.memory.add_insight(insight, source="document_analysis")
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing document {filename}: {e}")
            return DocumentAnalysis(
                document_type="unknown",
                language="de",
                extracted_data={},
                validation_issues=[f"Fehler bei Dokumentenanalyse: {str(e)}"],
                completeness_check={},
                confidence=0.0
            )
    
    async def process(self, receipts: List[Dict[str, Any]], encryption=None) -> List[DocumentAnalysis]:
        """
        Process multiple receipts
        Supports encrypted files for DSGVO compliance
        """
        analyses = []
        for receipt in receipts:
            analysis = await self.analyze_document(
                receipt.get("local_path", ""),
                receipt.get("filename", ""),
                encryption
            )
            
            # EU-AI-Act: Log AI decision
            try:
                from compliance import AITransparency
                ai_log = AITransparency.create_ai_decision_log(
                    decision_type="document_analysis",
                    agent_name=self.name,
                    input_data={"filename": receipt.get("filename"), "path": receipt.get("local_path")},
                    output_data=analysis.model_dump(),
                    confidence=analysis.confidence,
                    human_reviewed=False
                )
                # Store AI log in analysis metadata for transparency
                if not hasattr(analysis, 'ai_decision_log'):
                    analysis.ai_decision_log = ai_log
            except Exception as e:
                logger.warning(f"Could not create AI decision log: {e}")
            analyses.append(analysis)
            
            # Notify other agents about analysis completion (if message bus available)
            if self.message_bus:
                self.message_bus.publish(self.name, "AccountingAgent", {
                    "type": "document_analyzed",
                    "receipt_id": receipt.get("id"),
                    "analysis": analysis.model_dump()
                })
                
                # If issues found, notify Chat Agent
                if analysis.validation_issues or not all(analysis.completeness_check.values()):
                    self.message_bus.publish(self.name, "ChatAgent", {
                        "type": "document_issue",
                        "receipt_id": receipt.get("id"),
                        "filename": receipt.get("filename"),
                        "issues": analysis.validation_issues,
                        "completeness": analysis.completeness_check
                    })
        
        return analyses

class AccountingAgent:
    """Agent für Buchhaltung: Zuordnung, Verpflegungsmehraufwand, Spesensätze"""
    
    def __init__(self, llm: OllamaLLM, message_bus: Optional[AgentMessageBus] = None, memory: Optional[AgentMemory] = None, db=None, tools: Optional[AgentToolRegistry] = None):
        self.llm = llm
        self.name = "AccountingAgent"
        self.message_bus = message_bus
        self.memory = memory or AgentMemory(self.name, db)
        self.tools = tools or get_tool_registry()
        # Load prompt from markdown file
        self.system_prompt_base = load_prompt("accounting_agent.md")
        if not self.system_prompt_base:
            # Fallback default prompt
            self.system_prompt_base = """Du bist ein Buchhaltungs-Experte für Reisekostenabrechnungen.
Deine Aufgaben:
1. Dokumente den Reisekosteneinträgen zuordnen (basierend auf Datum, Ort, Zweck)
2. Verpflegungsmehraufwand automatisch berechnen (basierend auf Land und Abwesenheitsdauer)
3. Spezielle Dokumente zuordnen (Maut, Parken, etc.)
4. Kategorien korrekt zuweisen
5. Beträge validieren und korrigieren

Verfügbare Tools:
- geocoding: Bestimmt Ländercode aus Ortsangabe
- meal_allowance_lookup: Holt aktuelle Verpflegungsmehraufwand-Spesensätze
- currency_exchange: Rechnet Fremdwährungen in EUR um
- web_search: Sucht nach aktuellen Informationen"""
        
        # Subscribe to messages from other agents
        if self.message_bus:
            self.message_bus.subscribe(self.name, self.handle_agent_message)
    
    async def initialize(self):
        """Initialisiere Memory"""
        await self.memory.initialize()
    
    def handle_agent_message(self, message: Dict):
        """Handle messages from other agents"""
        logger.info(f"AccountingAgent received message from {message.get('from')}: {message.get('content')}")
        # Can request document analysis from Document Agent or clarification from Chat Agent
    
    async def get_country_code(self, location: str) -> str:
        """Get country code from location - nutzt Geocoding-Tool für aktuelle Daten"""
        try:
            # Versuche zuerst Geocoding-Tool
            geocoding_tool = self.tools.get_tool("geocoding")
            if geocoding_tool:
                result = await geocoding_tool.execute(location)
                if result.get("success") and result.get("country_code"):
                    country_code = result["country_code"]
                    # Speichere im Memory
                    await self.memory.add_insight(
                        f"Länderbestimmung für '{location}': {country_code} ({result.get('country', '')})",
                        source="geocoding_tool"
                    )
                    return country_code
        except Exception as e:
            logger.warning(f"Geocoding tool error: {e}, using fallback")
        
        # Fallback auf einfache String-Erkennung
        location_lower = location.lower()
        country_mapping = {
            "deutschland": "DE", "germany": "DE",
            "österreich": "AT", "austria": "AT",
            "schweiz": "CH", "switzerland": "CH",
            "frankreich": "FR", "france": "FR",
            "italien": "IT", "italy": "IT",
            "spanien": "ES", "spain": "ES",
            "großbritannien": "GB", "uk": "GB", "england": "GB",
            "usa": "US", "vereinigte staaten": "US"
        }
        for key, code in country_mapping.items():
            if key in location_lower:
                return code
        return "DE"  # Default: Deutschland
    
    async def get_meal_allowance(self, location: str, days: int, is_24h_absence: bool = True) -> float:
        """Get Verpflegungsmehraufwand based on location and duration - nutzt Web-Tools für aktuelle Daten"""
        country_code = await self.get_country_code(location)
        
        # Versuche zuerst aktuelle Spesensätze aus dem Web zu holen
        try:
            meal_allowance_tool = self.tools.get_tool("meal_allowance_lookup")
            if meal_allowance_tool:
                result = await meal_allowance_tool.execute(country_code)
                if result.get("success"):
                    if result.get("rates"):
                        rates_list = result["rates"]
                        if isinstance(rates_list, list) and len(rates_list) >= 2:
                            # Nimm die ersten beiden Werte (24h und abwesend)
                            rates = {
                                "24h": float(rates_list[0]),
                                "abwesend": float(rates_list[1]) if len(rates_list) > 1 else float(rates_list[0]) / 2
                            }
                            rate_type = "24h" if is_24h_absence else "abwesend"
                            daily_rate = rates.get(rate_type, rates["24h"])
                            
                            # Speichere im Memory
                            await self.memory.add_insight(
                                f"Aktuelle Spesensätze für {country_code}: 24h={rates['24h']} EUR, abwesend={rates['abwesend']} EUR (Quelle: Web)",
                                source="meal_allowance_lookup_tool"
                            )
                            
                            return daily_rate * days
                        elif isinstance(rates_list, dict):
                            # Falls es bereits ein Dict ist
                            rates = rates_list
                            rate_type = "24h" if is_24h_absence else "abwesend"
                            daily_rate = rates.get(rate_type, rates.get("24h", 28.0))
                            return daily_rate * days
        except Exception as e:
            logger.warning(f"Meal allowance lookup tool error: {e}, using local database")
        
        # Fallback auf lokale Datenbank
        rates = MEAL_ALLOWANCE_RATES.get(country_code, MEAL_ALLOWANCE_RATES["DEFAULT"])
        rate_type = "24h" if is_24h_absence else "abwesend"
        daily_rate = rates[rate_type]
        
        return daily_rate * days
    
    async def assign_expenses(self, report_entries: List[Dict], document_analyses: List[DocumentAnalysis], receipts: List[Dict]) -> List[ExpenseAssignment]:
        """Assign expenses to travel entries"""
        assignments = []
        
        # Create mapping of dates to entries
        entries_by_date = {entry.get("date"): entry for entry in report_entries}
        
        for i, analysis in enumerate(document_analyses):
            if i >= len(receipts):
                continue
            
            receipt = receipts[i]
            doc_date = analysis.extracted_data.get("date")
            doc_amount = analysis.extracted_data.get("amount", 0.0)
            
            # Find matching entry
            matching_entry = None
            if doc_date:
                matching_entry = entries_by_date.get(doc_date)
            
            # If no exact date match, use LLM to find best match
            if not matching_entry and report_entries:
                # Hole relevanten Memory-Kontext für ähnliche Zuordnungen
                memory_context = await self.memory.get_context_for_prompt(
                    max_tokens=1500,
                    relevant_query=f"assignment {analysis.document_type} {doc_date} {doc_amount}"
                )
                
                # Erweitere System-Prompt mit Memory
                system_prompt = self.system_prompt_base
                if memory_context:
                    system_prompt += f"\n\n=== Dein Gedächtnis (frühere Zuordnungen) ===\n{memory_context}\n"
                    system_prompt += "\nNutze diese Erfahrungen aus deinem Gedächtnis, um ähnliche Zuordnungen besser durchzuführen."
                
                prompt = f"""Ordne folgendes Dokument einem Reiseeintrag zu:

Dokument:
- Typ: {analysis.document_type}
- Betrag: {doc_amount} {analysis.extracted_data.get('currency', 'EUR')}
- Datum: {doc_date}
- Weitere Daten: {json.dumps(analysis.extracted_data, ensure_ascii=False, indent=2)}

Verfügbare Reiseeinträge:
{json.dumps([{"date": e.get("date"), "location": e.get("location"), "customer_project": e.get("customer_project"), "days_count": e.get("days_count", 1)} for e in report_entries], indent=2, ensure_ascii=False)}

Finde den besten passenden Reiseeintrag basierend auf:
- Datum (am besten)
- Ort/Standort
- Zweck/Projekt

Antworte mit JSON: {{"entry_date": "YYYY-MM-DD", "confidence": 0.0-1.0, "reason": "Warum dieser Eintrag passt"}}"""
                
                match_result = await self.llm.extract_json(prompt, system_prompt)
                if match_result and "entry_date" in match_result:
                    matching_entry = entries_by_date.get(match_result["entry_date"])
                    if matching_entry and match_result.get("confidence", 0.0) < 0.5:
                        # Low confidence - don't assign
                        matching_entry = None
            
            if matching_entry:
                # Determine category
                category = analysis.document_type
                if category == "restaurant_bill":
                    category = "meals"
                elif category in ["toll_receipt", "parking", "fuel"]:
                    category = "transport"
                elif category == "hotel_receipt":
                    category = "hotel"
                
                # Calculate meal allowance if applicable
                meal_allowance = None
                # Meal allowance is added separately for travel days, not for restaurant bills
                # Restaurant bills are actual expenses, meal allowance is for days without restaurant receipts
                
                # For hotel stays, calculate meal allowance for each day
                if category == "hotel":
                    location = matching_entry.get("location", "")
                    days = matching_entry.get("days_count", 1)
                    # Full day absence = 24h rate
                    meal_allowance = await self.get_meal_allowance(location, days, is_24h_absence=True)
                
                assignment = ExpenseAssignment(
                    receipt_id=receipt.get("id", ""),
                    entry_date=matching_entry.get("date", ""),
                    category=category,
                    amount=doc_amount,
                    currency=analysis.extracted_data.get("currency", "EUR"),
                    meal_allowance_added=meal_allowance,
                    assignment_confidence=analysis.confidence
                )
                
                # Speichere Zuordnung im Memory
                assignment_summary = f"Dokument {receipt.get('id', '')} zugeordnet zu Eintrag {assignment.entry_date}, Kategorie: {category}, Betrag: {doc_amount} {assignment.currency}"
                if meal_allowance:
                    assignment_summary += f", Verpflegungsmehraufwand: {meal_allowance} EUR"
                
                await self.memory.add_decision(
                    assignment_summary,
                    confidence=assignment.assignment_confidence,
                    context={
                        "document_type": analysis.document_type,
                        "category": category,
                        "entry_date": assignment.entry_date
                    }
                )
                
                assignments.append(assignment)
        
        return assignments
    
    async def process(self, report: Dict, document_analyses: List[DocumentAnalysis]) -> Dict[str, Any]:
        """Process expense assignment and meal allowance"""
        report_entries = report.get("entries", [])
        assignments = await self.assign_expenses(
            report_entries,
            document_analyses,
            report.get("receipts", [])
        )
        
        # Machbarkeitsprüfung: Überlappende Hotelrechnungen, Datum-Abgleich
        feasibility_issues = []
        
        # Prüfe auf überlappende Hotelrechnungen
        hotel_assignments = [a for a in assignments if a.category == "hotel"]
        hotel_dates = {}
        for assignment in hotel_assignments:
            entry_date = assignment.entry_date
            if entry_date in hotel_dates:
                hotel_dates[entry_date].append(assignment)
            else:
                hotel_dates[entry_date] = [assignment]
        
        for date, date_assignments in hotel_dates.items():
            if len(date_assignments) > 1:
                feasibility_issues.append(f"Mehrere Hotelrechnungen für {date} gefunden - mögliche Überlappung")
        
        # Prüfe Datum-Abgleich mit Arbeitsstunden
        for assignment in assignments:
            entry_date = assignment.entry_date
            matching_entry = next((e for e in report_entries if e.get("date") == entry_date), None)
            if matching_entry:
                working_hours = matching_entry.get("working_hours", 0.0)
                if working_hours == 0.0:
                    feasibility_issues.append(f"Für {entry_date} sind keine Arbeitsstunden im Stundenzettel verzeichnet, aber Reisekosten vorhanden")
        
        # Prüfe zeitliche Machbarkeit (Übernachtung ohne Anreise)
        entries_by_date = {e.get("date"): e for e in report_entries}
        for assignment in hotel_assignments:
            entry_date = assignment.entry_date
            from datetime import datetime, timedelta
            try:
                entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d")
                prev_date = (entry_date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
                # Prüfe, ob es einen Reiseeintrag am Tag davor gibt
                if prev_date not in entries_by_date:
                    feasibility_issues.append(f"Hotelrechnung für {entry_date}, aber kein Reiseeintrag am Tag davor - mögliche fehlende Anreise")
            except:
                pass
        
        # Calculate totals
        total_expenses = sum(a.amount for a in assignments)
        total_meal_allowance = sum(a.meal_allowance_added or 0.0 for a in assignments)
        
        # Also calculate meal allowance for entries without receipts (pure travel days)
        entries_with_receipts = {a.entry_date for a in assignments}
        for entry in report_entries:
            entry_date = entry.get("date")
            if entry_date not in entries_with_receipts:
                # Travel day without receipt - add meal allowance
                location = entry.get("location", "")
                days = entry.get("days_count", 1)
                meal_allowance = await self.get_meal_allowance(location, days, is_24h_absence=True)
                total_meal_allowance += meal_allowance
        
        result = {
            "assignments": [a.model_dump() for a in assignments],
            "total_expenses": round(total_expenses, 2),
            "total_meal_allowance": round(total_meal_allowance, 2),
            "feasibility_issues": feasibility_issues,
            "summary": f"Zuordnung abgeschlossen: {len(assignments)} Dokumente zugeordnet, Gesamtausgaben: {total_expenses:.2f} EUR, Verpflegungsmehraufwand: {total_meal_allowance:.2f} EUR"
        }
        
        if feasibility_issues:
            result["summary"] += f"\n⚠️ {len(feasibility_issues)} Machbarkeitsprobleme gefunden - bitte prüfen!"
        
        # Speichere Zusammenfassung im Memory
        await self.memory.add_insight(
            f"Buchhaltungszuordnung abgeschlossen: {len(assignments)} Dokumente, Gesamtausgaben: {total_expenses:.2f} EUR, Verpflegungsmehraufwand: {total_meal_allowance:.2f} EUR, Probleme: {len(feasibility_issues)}",
            source="process_completion"
        )
        
        return result

class AgentOrchestrator:
    """Orchestrates the agent network for expense report review"""
    
    def __init__(self, llm: Optional[OllamaLLM] = None, db=None):
        base_url = (llm.base_url if isinstance(llm, OllamaLLM) else OLLAMA_BASE_URL)
        self.chat_llm = OllamaLLM(base_url=base_url, model=OLLAMA_MODEL_CHAT)
        self.document_llm = OllamaLLM(base_url=base_url, model=OLLAMA_MODEL_DOCUMENT)
        self.accounting_llm = OllamaLLM(base_url=base_url, model=OLLAMA_MODEL_ACCOUNTING)
        self._llms = {
            "ChatAgent": self.chat_llm,
            "DocumentAgent": self.document_llm,
            "AccountingAgent": self.accounting_llm,
        }
        self.db = db
        self.message_bus = AgentMessageBus()
        # Initialisiere Tool-Registry
        self.tools = get_tool_registry()
        # Initialisiere Agenten mit Memory und Tools
        self.chat_agent = ChatAgent(self.chat_llm, db=db)
        self.document_agent = DocumentAgent(self.document_llm, self.message_bus, db=db)
        self.accounting_agent = AccountingAgent(self.accounting_llm, self.message_bus, db=db, tools=self.tools)
        self._llm_health_checked = False
        self._memory_initialized = False
    
    async def ensure_llm_available(self):
        """Check LLM availability and warn if not reachable"""
        if not self._llm_health_checked:
            all_healthy = True
            for agent_name, agent_llm in self._llms.items():
                is_healthy = await agent_llm.health_check()
                if not is_healthy:
                    all_healthy = False
                    logger.error(f"⚠️ Ollama LLM für {agent_name} nicht erreichbar: {agent_llm.base_url} (Modell: {agent_llm.model})")
                    logger.error("Bitte überprüfen Sie:")
                    logger.error("  1. Ollama läuft auf dem GMKTec-Server")
                    logger.error("  2. Netzwerk-Verbindung zum GMKTec-Server")
                    logger.error("  3. Firewall-Regeln erlauben Zugriff")
                    logger.error("  4. OLLAMA_BASE_URL und agentenspezifische Modelle sind korrekt konfiguriert")
                else:
                    logger.info(f"✅ Ollama LLM erreichbar für {agent_name}: {agent_llm.base_url} (Modell: {agent_llm.model})")
            self._llm_health_checked = True
            return all_healthy
        return True
    
    async def initialize_memory(self):
        """Initialisiere Memory für alle Agenten"""
        if not self._memory_initialized:
            await self.chat_agent.initialize()
            await self.document_agent.initialize()
            await self.accounting_agent.initialize()
            self._memory_initialized = True
            logger.info("Agent-Memory für alle Agenten initialisiert")
    
    def broadcast_message(self, from_agent: str, message: Dict[str, Any]):
        """Broadcast message to all agents via message bus"""
        self.message_bus.broadcast(from_agent, message)
    
    def send_message(self, from_agent: str, to_agent: str, message: Dict[str, Any]):
        """Send message from one agent to another"""
        self.message_bus.publish(from_agent, to_agent, message)
    
    async def close(self):
        """Clean up resources"""
        for agent_llm in self._llms.values():
            await agent_llm.close()
        # Schließe alle Tools
        await self.tools.close()
    
    async def review_expense_report(self, report_id: str, db) -> Dict[str, Any]:
        """Main orchestration method for reviewing an expense report"""
        # Ensure LLM is available
        await self.ensure_llm_available()
        
        # Initialisiere Memory
        await self.initialize_memory()
        
        # Fetch report
        report = await db.travel_expense_reports.find_one({"id": report_id})
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        receipts = report.get("receipts", [])
        entries = report.get("entries", [])
        
        # Step 1: Document Agent - Analyze all receipts
        logger.info(f"Step 1: Analyzing {len(receipts)} documents...")
        self.broadcast_message("Orchestrator", {
            "type": "status_update",
            "message": f"Starte Dokumentenanalyse für {len(receipts)} Belege",
            "step": 1
        })
        document_analyses = await self.document_agent.process(receipts)
        
        # Notify other agents about document analyses
        self.send_message("DocumentAgent", "AccountingAgent", {
            "type": "document_analyses_complete",
            "analyses": [a.model_dump() for a in document_analyses]
        })
        
        # Collect issues
        issues = []
        for analysis in document_analyses:
            if analysis.validation_issues:
                issues.extend(analysis.validation_issues)
            if not all(analysis.completeness_check.values()):
                issues.append(f"Dokument {analysis.document_type}: Vollständigkeitsprüfung fehlgeschlagen")
        
        # Step 2: Accounting Agent - Assign expenses and calculate meal allowance
        logger.info("Step 2: Assigning expenses...")
        self.broadcast_message("Orchestrator", {
            "type": "status_update",
            "message": "Starte Buchhaltungszuordnung",
            "step": 2
        })
        accounting_result = await self.accounting_agent.process(report, document_analyses)
        
        # Check if accounting agent needs clarification
        issues_needing_clarification = []
        for assignment in accounting_result.get("assignments", []):
            if assignment.get("assignment_confidence", 1.0) < 0.7:
                issues_needing_clarification.append({
                    "type": "low_confidence_assignment",
                    "receipt_id": assignment.get("receipt_id"),
                    "confidence": assignment.get("assignment_confidence")
                })
        
        # Step 3: Handle issues requiring clarification
        if issues_needing_clarification or issues:
            logger.info("Step 3: Issues found, may need user clarification")
            # Notify Chat Agent about issues
            self.send_message("Orchestrator", "ChatAgent", {
                "type": "clarification_needed",
                "document_issues": issues,
                "assignment_issues": issues_needing_clarification
            })
        
        # Step 4: Generate review summary
        review_summary = f"""Reisekostenabrechnung geprüft:

Dokumentenanalyse:
- {len(document_analyses)} Dokumente analysiert
- Probleme gefunden: {len(issues)}

Buchhaltungszuordnung:
{accounting_result['summary']}

Zuordnung:
{json.dumps(accounting_result['assignments'], indent=2, ensure_ascii=False)}

Status: {'Benötigt Klärung' if (issues_needing_clarification or issues) else 'Prüfung abgeschlossen'}
"""
        
        # Notify all agents about completion
        self.broadcast_message("Orchestrator", {
            "type": "review_complete",
            "has_issues": bool(issues_needing_clarification or issues),
            "summary": review_summary
        })
        
        # Update report with review notes
        await db.travel_expense_reports.update_one(
            {"id": report_id},
            {
                "$set": {
                    "review_notes": review_summary,
                    "accounting_data": accounting_result,
                    "document_analyses": [a.model_dump() for a in document_analyses],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Determine if user input is needed
        requires_input = len(issues) > 0
        
        return {
            "status": "review_complete" if not requires_input else "needs_user_input",
            "issues": issues,
            "accounting_result": accounting_result,
            "document_analyses": [a.model_dump() for a in document_analyses],
            "requires_user_input": requires_input
        }
    
    async def handle_user_message(self, report_id: str, user_message: str, db) -> AgentResponse:
        """Handle user message in chat context"""
        # Initialisiere Memory
        await self.initialize_memory()
        
        report = await db.travel_expense_reports.find_one({"id": report_id})
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Get review context
        context = {
            "report": report,
            "issues": report.get("review_notes", "").split("\n") if report.get("review_notes") else [],
            "missing_info": []  # Would be extracted from review notes
        }
        
        # Process with Chat Agent
        response = await self.chat_agent.process(context, user_message)
        
        # Save chat message
        from server import ChatMessage
        chat_msg = ChatMessage(
            report_id=report_id,
            sender="agent",
            message=response.message
        )
        chat_msg_dict = chat_msg.model_dump()
        chat_msg_dict["created_at"] = datetime.utcnow()
        await db.chat_messages.insert_one(chat_msg_dict)
        
        return response

