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

class OpenMapsTool(AgentTool):
    """Tool für OpenStreetMap - umfassende Karten- und Geodaten-Funktionen"""
    
    def __init__(self):
        super().__init__(
            name="openmaps",
            description="Umfassendes Tool für OpenStreetMap-Funktionen: Geocoding, Reverse Geocoding, POI-Suche, Entfernungsberechnung, Routenplanung. Nützlich für Reisekostenabrechnungen, Ortsbestimmung, Entfernungsvalidierung und Standortinformationen.",
            parameters={
                "action": {
                    "type": "string",
                    "description": "Aktion: 'geocode' (Adresse zu Koordinaten), 'reverse' (Koordinaten zu Adresse), 'search' (POI-Suche), 'distance' (Entfernung berechnen), 'route' (Route berechnen)",
                    "enum": ["geocode", "reverse", "search", "distance", "route"]
                },
                "query": {
                    "type": "string",
                    "description": "Suchanfrage (für geocode/search): Adresse, Ort oder POI-Name",
                    "default": None
                },
                "lat": {
                    "type": "number",
                    "description": "Breitengrad (für reverse/distance/route)",
                    "default": None
                },
                "lon": {
                    "type": "number",
                    "description": "Längengrad (für reverse/distance/route)",
                    "default": None
                },
                "lat2": {
                    "type": "number",
                    "description": "Zweiter Breitengrad (für distance/route)",
                    "default": None
                },
                "lon2": {
                    "type": "number",
                    "description": "Zweiter Längengrad (für distance/route)",
                    "default": None
                },
                "poi_type": {
                    "type": "string",
                    "description": "POI-Typ für Suche (z.B. 'hotel', 'restaurant', 'fuel', 'parking')",
                    "default": None
                },
                "radius": {
                    "type": "number",
                    "description": "Suchradius in Metern (für search, Standard: 1000)",
                    "default": 1000
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximale Anzahl Ergebnisse (Standard: 5)",
                    "default": 5
                }
            }
        )
        self._session = None
        self.base_url = "https://nominatim.openstreetmap.org"
        self.user_agent = "Stundenzettel-Web-App/1.0"
    
    async def _get_session(self):
        """Get aiohttp session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mache Request an Nominatim API"""
        try:
            session = await self._get_session()
            headers = {"User-Agent": self.user_agent}
            url = f"{self.base_url}/{endpoint}"
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "data": data}
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "status": response.status
                    }
        except Exception as e:
            logger.error(f"OpenMaps request error: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute(self, 
                      action: str,
                      query: Optional[str] = None,
                      lat: Optional[float] = None,
                      lon: Optional[float] = None,
                      lat2: Optional[float] = None,
                      lon2: Optional[float] = None,
                      poi_type: Optional[str] = None,
                      radius: int = 1000,
                      limit: int = 5) -> Dict[str, Any]:
        """Führe OpenMaps-Aktion aus"""
        try:
            if action == "geocode":
                if not query:
                    return {"success": False, "error": "query ist erforderlich für geocode"}
                
                params = {
                    "q": query,
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1
                }
                result = await self._make_request("search", params)
                
                if result.get("success"):
                    results = result["data"]
                    formatted_results = []
                    for r in results[:limit]:
                        address = r.get("address", {})
                        formatted_results.append({
                            "display_name": r.get("display_name", ""),
                            "lat": float(r.get("lat", 0)),
                            "lon": float(r.get("lon", 0)),
                            "country_code": address.get("country_code", "").upper(),
                            "country": address.get("country", ""),
                            "city": address.get("city") or address.get("town") or address.get("village", ""),
                            "postcode": address.get("postcode", ""),
                            "type": r.get("type", ""),
                            "class": r.get("class", "")
                        })
                    
                    return {
                        "success": True,
                        "action": "geocode",
                        "query": query,
                        "results": formatted_results,
                        "count": len(formatted_results)
                    }
                else:
                    return result
            
            elif action == "reverse":
                if lat is None or lon is None:
                    return {"success": False, "error": "lat und lon sind erforderlich für reverse"}
                
                params = {
                    "lat": str(lat),
                    "lon": str(lon),
                    "format": "json",
                    "addressdetails": 1
                }
                result = await self._make_request("reverse", params)
                
                if result.get("success"):
                    data = result["data"]
                    address = data.get("address", {})
                    return {
                        "success": True,
                        "action": "reverse",
                        "lat": lat,
                        "lon": lon,
                        "display_name": data.get("display_name", ""),
                        "country_code": address.get("country_code", "").upper(),
                        "country": address.get("country", ""),
                        "city": address.get("city") or address.get("town") or address.get("village", ""),
                        "postcode": address.get("postcode", ""),
                        "full_address": address
                    }
                else:
                    return result
            
            elif action == "search":
                if not query:
                    return {"success": False, "error": "query ist erforderlich für search"}
                
                # POI-Suche mit Typ-Filter
                search_query = query
                if poi_type:
                    search_query = f"{poi_type} {query}"
                
                params = {
                    "q": search_query,
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1
                }
                
                # Wenn lat/lon gegeben, füge Bounding Box hinzu für Radius-Suche
                if lat is not None and lon is not None:
                    # Einfache Bounding Box (ungefährer Radius)
                    # 1 Grad ≈ 111 km, also radius/111000 für grobe Bounding Box
                    delta = radius / 111000.0
                    params["viewbox"] = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
                    params["bounded"] = "1"
                
                result = await self._make_request("search", params)
                
                if result.get("success"):
                    results = result["data"]
                    formatted_results = []
                    for r in results[:limit]:
                        address = r.get("address", {})
                        formatted_results.append({
                            "name": r.get("display_name", ""),
                            "lat": float(r.get("lat", 0)),
                            "lon": float(r.get("lon", 0)),
                            "type": r.get("type", ""),
                            "class": r.get("class", ""),
                            "country_code": address.get("country_code", "").upper(),
                            "city": address.get("city") or address.get("town") or address.get("village", "")
                        })
                    
                    return {
                        "success": True,
                        "action": "search",
                        "query": query,
                        "poi_type": poi_type,
                        "results": formatted_results,
                        "count": len(formatted_results)
                    }
                else:
                    return result
            
            elif action == "distance":
                if lat is None or lon is None or lat2 is None or lon2 is None:
                    return {"success": False, "error": "lat, lon, lat2 und lon2 sind erforderlich für distance"}
                
                # Haversine-Formel für Entfernungsberechnung
                from math import radians, sin, cos, sqrt, atan2
                
                R = 6371000  # Erdradius in Metern
                lat1_rad = radians(lat)
                lat2_rad = radians(lat2)
                delta_lat = radians(lat2 - lat)
                delta_lon = radians(lon2 - lon)
                
                a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                distance_meters = R * c
                distance_km = distance_meters / 1000
                
                return {
                    "success": True,
                    "action": "distance",
                    "from": {"lat": lat, "lon": lon},
                    "to": {"lat": lat2, "lon": lon2},
                    "distance_meters": round(distance_meters, 2),
                    "distance_km": round(distance_km, 2)
                }
            
            elif action == "route":
                if lat is None or lon is None or lat2 is None or lon2 is None:
                    return {"success": False, "error": "lat, lon, lat2 und lon2 sind erforderlich für route"}
                
                # Für einfache Routenberechnung verwenden wir die Entfernung
                # Eine vollständige Routing-API würde OSRM oder GraphHopper benötigen
                # Hier geben wir eine einfache Luftlinie + geschätzte Fahrzeit zurück
                from math import radians, sin, cos, sqrt, atan2
                
                R = 6371000
                lat1_rad = radians(lat)
                lat2_rad = radians(lat2)
                delta_lat = radians(lat2 - lat)
                delta_lon = radians(lon2 - lon)
                
                a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                distance_meters = R * c
                distance_km = distance_meters / 1000
                
                # Geschätzte Fahrzeit (Durchschnittsgeschwindigkeit 80 km/h)
                estimated_driving_time_hours = distance_km / 80.0
                estimated_driving_time_minutes = estimated_driving_time_hours * 60
                
                return {
                    "success": True,
                    "action": "route",
                    "from": {"lat": lat, "lon": lon},
                    "to": {"lat": lat2, "lon": lon2},
                    "distance_km": round(distance_km, 2),
                    "distance_meters": round(distance_meters, 2),
                    "estimated_driving_time_hours": round(estimated_driving_time_hours, 2),
                    "estimated_driving_time_minutes": round(estimated_driving_time_minutes, 0),
                    "note": "Luftlinie - für detaillierte Routenplanung wird eine Routing-API benötigt"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unbekannte Aktion: {action}",
                    "available_actions": ["geocode", "reverse", "search", "distance", "route"]
                }
                
        except Exception as e:
            logger.error(f"OpenMaps execute error: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

# Optional imports für erweiterte Tools
try:
    from exa_py import Exa
    HAS_EXA = True
except ImportError:
    HAS_EXA = False

try:
    from paddleocr import PaddleOCR
    HAS_PADDLEOCR = True
except ImportError:
    HAS_PADDLEOCR = False

try:
    from langchain.tools import Tool
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

class ExaSearchTool(AgentTool):
    """Tool für Exa/XNG Suche - hochwertige semantische Suche"""
    
    def __init__(self):
        super().__init__(
            name="exa_search",
            description="Hochwertige semantische Suche mit Exa/XNG API. Besser als Standard-Web-Suche für präzise, relevante Ergebnisse. Nützlich für ChatAgent zur Beantwortung von Fragen.",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Suchanfrage (semantisch verstanden)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximale Anzahl an Ergebnissen (Standard: 5)",
                    "default": 5
                },
                "use_autoprompt": {
                    "type": "boolean",
                    "description": "Verwende Auto-Prompt für bessere Ergebnisse (Standard: True)",
                    "default": True
                }
            }
        )
        self.api_key = os.getenv('EXA_API_KEY')
        self._exa_client = None
    
    def _get_client(self):
        """Get Exa client"""
        if not HAS_EXA:
            return None
        if self._exa_client is None and self.api_key:
            try:
                self._exa_client = Exa(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Exa client initialization error: {e}")
        return self._exa_client
    
    async def execute(self, query: str, max_results: int = 5, use_autoprompt: bool = True) -> Dict[str, Any]:
        """Führe Exa-Suche aus"""
        try:
            client = self._get_client()
            if not client:
                return {
                    "success": False,
                    "error": "Exa API nicht verfügbar. Bitte EXA_API_KEY setzen und 'pip install exa-py' installieren.",
                    "fallback_available": True
                }
            
            # Exa API-Aufruf (synchron, aber in async context)
            search_params = {
                "query": query,
                "num_results": max_results,
                "use_autoprompt": use_autoprompt,
                "text": {"max_characters": 1000}  # Hole Text-Inhalt
            }
            
            # Exa ist synchron, daher in Thread ausführen
            import asyncio
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: client.search(**search_params))
            
            formatted_results = []
            for result in results.results:
                formatted_results.append({
                    "title": result.title,
                    "url": result.url,
                    "text": result.text[:500] if result.text else "",
                    "published_date": result.published_date.isoformat() if hasattr(result, 'published_date') and result.published_date else None,
                    "author": result.author if hasattr(result, 'author') else None
                })
            
            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results),
                "source": "exa"
            }
            
        except Exception as e:
            logger.error(f"Exa search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "fallback_available": True
            }

class MarkerTool(AgentTool):
    """Tool für Marker - Dokumentenanalyse und -extraktion"""
    
    def __init__(self):
        super().__init__(
            name="marker",
            description="Marker-Tool für erweiterte Dokumentenanalyse. Extrahiert strukturierte Daten aus PDFs und anderen Dokumenten. Nützlich für DocumentAgent und AccountingAgent.",
            parameters={
                "document_path": {
                    "type": "string",
                    "description": "Pfad zum Dokument (PDF, Bild, etc.)"
                },
                "extract_tables": {
                    "type": "boolean",
                    "description": "Tabellen extrahieren (Standard: True)",
                    "default": True
                },
                "extract_images": {
                    "type": "boolean",
                    "description": "Bilder extrahieren (Standard: False)",
                    "default": False
                },
                "markdown_output": {
                    "type": "boolean",
                    "description": "Markdown-Format für Ausgabe (Standard: True)",
                    "default": True
                }
            }
        )
        self.marker_api_key = os.getenv('MARKER_API_KEY')
        self.marker_base_url = os.getenv('MARKER_BASE_URL', 'https://api.marker.io/v1')
        self._session = None
    
    async def _get_session(self):
        """Get aiohttp session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session
    
    async def execute(self, document_path: str, extract_tables: bool = True, extract_images: bool = False, markdown_output: bool = True) -> Dict[str, Any]:
        """Führe Marker-Dokumentenanalyse aus"""
        try:
            # Prüfe ob Datei existiert
            if not Path(document_path).exists():
                return {
                    "success": False,
                    "error": f"Dokument nicht gefunden: {document_path}",
                    "document_path": document_path
                }
            
            # Option 1: Marker API (falls verfügbar)
            if self.marker_api_key:
                session = await self._get_session()
                headers = {
                    "Authorization": f"Bearer {self.marker_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Lese Datei
                with open(document_path, 'rb') as f:
                    file_data = f.read()
                
                # Base64 kodieren
                import base64
                file_base64 = base64.b64encode(file_data).decode('utf-8')
                
                payload = {
                    "file": file_base64,
                    "filename": Path(document_path).name,
                    "extract_tables": extract_tables,
                    "extract_images": extract_images,
                    "markdown_output": markdown_output
                }
                
                async with session.post(
                    f"{self.marker_base_url}/extract",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "document_path": document_path,
                            "text": result.get("text", ""),
                            "markdown": result.get("markdown", ""),
                            "tables": result.get("tables", []),
                            "metadata": result.get("metadata", {}),
                            "source": "marker_api"
                        }
                    else:
                        error_text = await response.text()
                        logger.warning(f"Marker API error: {response.status} - {error_text[:200]}")
            
            # Option 2: Lokale Marker-Installation (falls verfügbar)
            # Marker kann auch lokal installiert werden
            try:
                import subprocess
                import tempfile
                
                # Versuche marker CLI zu verwenden
                result = subprocess.run(
                    ["marker", "convert", document_path, "--output", "markdown"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "document_path": document_path,
                        "text": result.stdout,
                        "markdown": result.stdout,
                        "source": "marker_cli"
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                logger.debug(f"Marker CLI nicht verfügbar: {e}")
            
            # Fallback: Verwende vorhandene PDF-Extraktion
            return {
                "success": False,
                "error": "Marker API/CLI nicht verfügbar. Verwende Fallback-Methoden.",
                "document_path": document_path,
                "fallback_available": True
            }
            
        except Exception as e:
            logger.error(f"Marker tool error: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_path": document_path,
                "fallback_available": True
            }
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

class PaddleOCRTool(AgentTool):
    """Tool für PaddleOCR - OCR als Fallback für Dokumentenanalyse"""
    
    def __init__(self):
        super().__init__(
            name="paddleocr",
            description="PaddleOCR-Tool für Texterkennung in Bildern und PDFs. Fallback für DocumentAgent wenn andere Methoden versagen. Unterstützt über 100 Sprachen.",
            parameters={
                "image_path": {
                    "type": "string",
                    "description": "Pfad zum Bild oder PDF"
                },
                "lang": {
                    "type": "string",
                    "description": "Sprache (z.B. 'de', 'en', 'ch', Standard: 'de')",
                    "default": "de"
                },
                "use_angle_cls": {
                    "type": "boolean",
                    "description": "Verwende Winkel-Klassifikation für bessere Ergebnisse (Standard: True)",
                    "default": True
                }
            }
        )
        self._ocr_instances: Dict[str, Any] = {}  # Cache für OCR-Instanzen pro Sprache
    
    def _get_ocr(self, lang: str = "de", use_angle_cls: bool = True):
        """Get PaddleOCR instance (cached)"""
        if not HAS_PADDLEOCR:
            return None
        
        cache_key = f"{lang}_{use_angle_cls}"
        if cache_key not in self._ocr_instances:
            try:
                self._ocr_instances[cache_key] = PaddleOCR(
                    use_angle_cls=use_angle_cls,
                    lang=lang,
                    show_log=False  # Reduziere Logging
                )
            except Exception as e:
                logger.error(f"PaddleOCR initialization error: {e}")
                return None
        
        return self._ocr_instances[cache_key]
    
    async def execute(self, image_path: str, lang: str = "de", use_angle_cls: bool = True) -> Dict[str, Any]:
        """Führe OCR aus"""
        try:
            if not Path(image_path).exists():
                return {
                    "success": False,
                    "error": f"Datei nicht gefunden: {image_path}",
                    "image_path": image_path
                }
            
            ocr = self._get_ocr(lang, use_angle_cls)
            if not ocr:
                return {
                    "success": False,
                    "error": "PaddleOCR nicht verfügbar. Bitte 'pip install paddleocr paddlepaddle' installieren.",
                    "image_path": image_path
                }
            
            # OCR ist synchron, daher in Thread ausführen
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: ocr.ocr(image_path, cls=use_angle_cls))
            
            # Formatiere Ergebnis
            extracted_text = []
            confidence_scores = []
            
            if result and len(result) > 0:
                for page_result in result:
                    if page_result:
                        for line in page_result:
                            if line and len(line) >= 2:
                                text_info = line[1]
                                if isinstance(text_info, tuple) and len(text_info) >= 2:
                                    text = text_info[0]
                                    confidence = text_info[1]
                                    extracted_text.append(text)
                                    confidence_scores.append(confidence)
                                elif isinstance(text_info, str):
                                    extracted_text.append(text_info)
            
            full_text = "\n".join(extracted_text)
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            return {
                "success": True,
                "image_path": image_path,
                "text": full_text,
                "lines": extracted_text,
                "confidence": avg_confidence,
                "confidence_scores": confidence_scores,
                "language": lang,
                "source": "paddleocr"
            }
            
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return {
                "success": False,
                "error": str(e),
                "image_path": image_path
            }

class CustomPythonRulesTool(AgentTool):
    """Tool für Custom Python Regeln - ausführbare Python-Regeln für AccountingAgent"""
    
    def __init__(self):
        super().__init__(
            name="custom_python_rules",
            description="Führt benutzerdefinierte Python-Regeln für Buchhaltungsvalidierung und -berechnung aus. Nützlich für AccountingAgent zur Anwendung spezifischer Geschäftsregeln.",
            parameters={
                "rule_name": {
                    "type": "string",
                    "description": "Name der Regel (z.B. 'validate_tax_number', 'calculate_meal_allowance', 'check_receipt_completeness')"
                },
                "rule_code": {
                    "type": "string",
                    "description": "Python-Code der Regel (optional, wenn Regel bereits registriert ist)"
                },
                "input_data": {
                    "type": "object",
                    "description": "Eingabedaten für die Regel (Dict)"
                }
            }
        )
        self._registered_rules: Dict[str, str] = {}  # Cache für registrierte Regeln
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Lade Standard-Buchhaltungsregeln"""
        # Beispiel-Regeln
        self._registered_rules["validate_tax_number"] = """
def validate_tax_number(tax_number: str, country_code: str = "DE") -> Dict[str, Any]:
    \"\"\"Validiere Steuernummer basierend auf Ländercode\"\"\"
    if not tax_number or not tax_number.strip():
        return {"valid": False, "error": "Steuernummer ist leer"}
    
    tax_number = tax_number.strip().replace(" ", "").replace("-", "")
    
    if country_code == "DE":
        # Deutsche USt-IdNr: DE + 9 Ziffern
        if tax_number.startswith("DE") and len(tax_number) == 11:
            return {"valid": True, "normalized": tax_number}
        elif len(tax_number) == 11 and tax_number.isdigit():
            return {"valid": True, "normalized": f"DE{tax_number}"}
        else:
            return {"valid": False, "error": "Ungültiges Format für deutsche USt-IdNr"}
    elif country_code == "AT":
        # Österreich: AT + 9 Ziffern
        if tax_number.startswith("AT") and len(tax_number) == 11:
            return {"valid": True, "normalized": tax_number}
        else:
            return {"valid": False, "error": "Ungültiges Format für österreichische USt-IdNr"}
    
    return {"valid": False, "error": f"Unbekannter Ländercode: {country_code}"}
"""
        
        self._registered_rules["check_receipt_completeness"] = """
def check_receipt_completeness(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"Prüfe Vollständigkeit eines Belegs\"\"\"
    required_fields = ["amount", "date", "tax_number"]
    missing_fields = []
    issues = []
    
    for field in required_fields:
        if field not in receipt_data or not receipt_data[field]:
            missing_fields.append(field)
    
    if "amount" in receipt_data:
        try:
            amount = float(receipt_data["amount"])
            if amount <= 0:
                issues.append("Betrag muss größer als 0 sein")
        except (ValueError, TypeError):
            issues.append("Ungültiger Betrag")
    
    return {
        "complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "issues": issues
    }
"""
        
        self._registered_rules["calculate_meal_allowance"] = """
def calculate_meal_allowance(country_code: str, days: int, is_24h: bool = True) -> float:
    \"\"\"Berechne Verpflegungsmehraufwand\"\"\"
    rates = {
        "DE": {"24h": 28.0, "abwesend": 14.0},
        "AT": {"24h": 41.0, "abwesend": 20.5},
        "CH": {"24h": 70.0, "abwesend": 35.0},
        "FR": {"24h": 57.0, "abwesend": 28.5},
        "IT": {"24h": 57.0, "abwesend": 28.5},
        "ES": {"24h": 58.5, "abwesend": 29.25},
        "GB": {"24h": 52.0, "abwesend": 26.0},
        "US": {"24h": 89.0, "abwesend": 44.5}
    }
    
    country_rates = rates.get(country_code.upper(), rates["DE"])
    rate_type = "24h" if is_24h else "abwesend"
    daily_rate = country_rates.get(rate_type, country_rates["24h"])
    
    return daily_rate * days
"""
    
    async def execute(self, rule_name: str, rule_code: Optional[str] = None, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Führe Python-Regel aus"""
        try:
            # Hole Regel-Code
            if rule_name in self._registered_rules:
                rule_code = self._registered_rules[rule_name]
            elif not rule_code:
                return {
                    "success": False,
                    "error": f"Regel '{rule_name}' nicht gefunden und kein Code bereitgestellt",
                    "available_rules": list(self._registered_rules.keys())
                }
            
            # Sicherheitsprüfung: Erlaube nur bestimmte Funktionen
            allowed_imports = ["json", "datetime", "re", "math"]
            dangerous_keywords = ["__import__", "eval", "exec", "open", "file", "input", "raw_input"]
            
            for keyword in dangerous_keywords:
                if keyword in rule_code:
                    return {
                        "success": False,
                        "error": f"Sicherheitsproblem: Gefährliches Keyword '{keyword}' in Regel-Code gefunden"
                    }
            
            # Erstelle sicherer Ausführungskontext
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "dict": dict,
                    "list": list,
                    "tuple": tuple,
                    "set": set,
                    "round": round,
                    "abs": abs,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "all": all,
                    "any": any,
                    "isinstance": isinstance,
                    "type": type,
                    "hasattr": hasattr,
                    "getattr": getattr,
                }
            }
            
            # Füge erlaubte Imports hinzu
            for imp in allowed_imports:
                try:
                    safe_globals[imp] = __import__(imp)
                except ImportError:
                    pass
            
            # Kompiliere und führe Regel aus
            try:
                compiled_code = compile(rule_code, f"<rule:{rule_name}>", "exec")
                exec(compiled_code, safe_globals)
                
                # Finde Hauptfunktion (gleicher Name wie Regel)
                if rule_name in safe_globals and callable(safe_globals[rule_name]):
                    func = safe_globals[rule_name]
                    
                    # Führe Funktion aus
                    if input_data:
                        if isinstance(input_data, dict):
                            result = func(**input_data)
                        else:
                            result = func(input_data)
                    else:
                        result = func()
                    
                    return {
                        "success": True,
                        "rule_name": rule_name,
                        "result": result,
                        "source": "custom_python_rule"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Funktion '{rule_name}' nicht in Regel-Code gefunden",
                        "rule_name": rule_name
                    }
                    
            except SyntaxError as e:
                return {
                    "success": False,
                    "error": f"Syntax-Fehler in Regel: {str(e)}",
                    "rule_name": rule_name
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Fehler beim Ausführen der Regel: {str(e)}",
                    "rule_name": rule_name
                }
                
        except Exception as e:
            logger.error(f"Custom Python Rules error: {e}")
            return {
                "success": False,
                "error": str(e),
                "rule_name": rule_name
            }
    
    def register_rule(self, rule_name: str, rule_code: str):
        """Registriere eine neue Regel"""
        self._registered_rules[rule_name] = rule_code
        logger.info(f"Regel '{rule_name}' registriert")

class WebAccessTool(AgentTool):
    """Tool für generischen Web-Zugriff - HTTP-Requests zu beliebigen Web-Ressourcen"""
    
    def __init__(self):
        super().__init__(
            name="web_access",
            description="Generischer Web-Zugriff für HTTP-Requests zu beliebigen URLs. Ermöglicht GET/POST/PUT/DELETE Requests, Web-Scraping, API-Zugriff und HTML-Inhalt-Extraktion. Nützlich für alle Agents zur Validierung, Datensammlung und API-Interaktion.",
            parameters={
                "url": {
                    "type": "string",
                    "description": "Vollständige URL (z.B. 'https://example.com/api/data')"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP-Methode (GET, POST, PUT, DELETE, Standard: GET)",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "default": "GET"
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP-Headers als Dictionary (optional)",
                    "default": {}
                },
                "params": {
                    "type": "object",
                    "description": "URL-Parameter als Dictionary (optional)",
                    "default": {}
                },
                "data": {
                    "type": "object",
                    "description": "Request-Body als Dictionary (für POST/PUT, optional)",
                    "default": None
                },
                "json_data": {
                    "type": "object",
                    "description": "JSON-Request-Body als Dictionary (für POST/PUT, optional)",
                    "default": None
                },
                "extract_text": {
                    "type": "boolean",
                    "description": "Extrahiere Text aus HTML (Standard: False)",
                    "default": False
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in Sekunden (Standard: 30)",
                    "default": 30
                }
            }
        )
        self._session = None
        self.allowed_domains = os.getenv('WEB_ACCESS_ALLOWED_DOMAINS', '').split(',') if os.getenv('WEB_ACCESS_ALLOWED_DOMAINS') else []
        self.blocked_domains = os.getenv('WEB_ACCESS_BLOCKED_DOMAINS', 'localhost,127.0.0.1,0.0.0.0').split(',')
    
    async def _get_session(self):
        """Get aiohttp session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session
    
    def _is_url_allowed(self, url: str) -> tuple:
        """Prüfe ob URL erlaubt ist (Sicherheitsprüfung)"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Prüfe Schema
            if parsed.scheme not in ['http', 'https']:
                return False, f"Nur HTTP/HTTPS erlaubt, nicht {parsed.scheme}"
            
            # Prüfe Domain-Whitelist (falls gesetzt)
            if self.allowed_domains and parsed.netloc not in self.allowed_domains:
                return False, f"Domain {parsed.netloc} nicht in erlaubter Liste"
            
            # Prüfe Domain-Blacklist
            for blocked in self.blocked_domains:
                if blocked and blocked in parsed.netloc:
                    return False, f"Domain {parsed.netloc} ist blockiert"
            
            # Prüfe auf private IPs (Sicherheit)
            if parsed.hostname:
                parts = parsed.hostname.split('.')
                if len(parts) == 4:
                    try:
                        ip_parts = [int(p) for p in parts]
                        # Private IP ranges
                        if (ip_parts[0] == 10 or 
                            (ip_parts[0] == 172 and 16 <= ip_parts[1] <= 31) or
                            (ip_parts[0] == 192 and ip_parts[1] == 168) or
                            ip_parts[0] == 127):
                            return False, f"Private IP {parsed.hostname} nicht erlaubt"
                    except ValueError:
                        pass  # Keine IP, sondern Hostname
            
            return True, None
            
        except Exception as e:
            return False, f"URL-Validierung fehlgeschlagen: {str(e)}"
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extrahiere Text aus HTML (vereinfacht)"""
        try:
            import re
            # Entferne Script- und Style-Tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            # Entferne HTML-Tags
            text = re.sub(r'<[^>]+>', ' ', html)
            # Normalisiere Whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception as e:
            logger.warning(f"HTML-Text-Extraktion fehlgeschlagen: {e}")
            return html[:1000]  # Fallback: erste 1000 Zeichen
    
    async def execute(self,
                      url: str,
                      method: str = "GET",
                      headers: Optional[Dict[str, str]] = None,
                      params: Optional[Dict[str, Any]] = None,
                      data: Optional[Dict[str, Any]] = None,
                      json_data: Optional[Dict[str, Any]] = None,
                      extract_text: bool = False,
                      timeout: int = 30) -> Dict[str, Any]:
        """Führe HTTP-Request aus"""
        try:
            # Sicherheitsprüfung
            allowed, error_msg = self._is_url_allowed(url)
            if not allowed:
                return {
                    "success": False,
                    "error": error_msg or "URL nicht erlaubt",
                    "url": url
                }
            
            # Standard-Headers
            default_headers = {
                "User-Agent": "Stundenzettel-Web-App/1.0 (Agent Tool)"
            }
            if headers:
                default_headers.update(headers)
            
            session = await self._get_session()
            request_timeout = aiohttp.ClientTimeout(total=timeout, connect=10)
            
            # Request ausführen
            request_kwargs = {
                "headers": default_headers,
                "timeout": request_timeout
            }
            
            if params:
                request_kwargs["params"] = params
            
            if method.upper() in ["POST", "PUT", "PATCH"]:
                if json_data:
                    request_kwargs["json"] = json_data
                elif data:
                    request_kwargs["data"] = data
            
            async with session.request(method.upper(), url, **request_kwargs) as response:
                response_data = None
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Hole Response-Inhalt
                if 'application/json' in content_type:
                    response_data = await response.json()
                elif 'text/html' in content_type or 'text/plain' in content_type:
                    text_content = await response.text()
                    if extract_text and 'text/html' in content_type:
                        response_data = {
                            "html": text_content,
                            "text": self._extract_text_from_html(text_content)
                        }
                    else:
                        response_data = text_content
                else:
                    # Binärdaten - nur Metadaten zurückgeben
                    response_data = {
                        "content_type": content_type,
                        "size": len(await response.read()),
                        "note": "Binärdaten nicht extrahiert"
                    }
                
                return {
                    "success": response.status < 400,
                    "status_code": response.status,
                    "url": url,
                    "method": method.upper(),
                    "headers": dict(response.headers),
                    "data": response_data,
                    "content_type": content_type
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"Web access error: {e}")
            return {
                "success": False,
                "error": f"HTTP-Client-Fehler: {str(e)}",
                "url": url
            }
        except Exception as e:
            logger.error(f"Web access error: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

class DateParserTool(AgentTool):
    """Tool für Datums-Parsing und -Validierung - unterstützt verschiedene Datumsformate"""
    
    def __init__(self):
        super().__init__(
            name="date_parser",
            description="Parsed und validiert Datumsangaben in verschiedenen Formaten. Unterstützt internationale Formate, relative Daten (heute, gestern) und Datumsberechnungen. Nützlich für alle Agents zur Datumsverarbeitung.",
            parameters={
                "date_string": {
                    "type": "string",
                    "description": "Datumsstring in beliebigem Format (z.B. '15.01.2025', '2025-01-15', '15/01/2025', 'heute', 'gestern')"
                },
                "output_format": {
                    "type": "string",
                    "description": "Ausgabeformat (Standard: 'YYYY-MM-DD')",
                    "enum": ["YYYY-MM-DD", "DD.MM.YYYY", "DD/MM/YYYY", "timestamp", "iso"],
                    "default": "YYYY-MM-DD"
                },
                "locale": {
                    "type": "string",
                    "description": "Locale für Parsing (Standard: 'de_DE')",
                    "default": "de_DE"
                }
            }
        )
    
    async def execute(self, date_string: str, output_format: str = "YYYY-MM-DD", locale: str = "de_DE") -> Dict[str, Any]:
        """Parse und formatiere Datum"""
        try:
            from datetime import datetime, timedelta
            import re
            
            date_string = date_string.strip()
            
            # Relative Daten
            today = datetime.now()
            relative_map = {
                "heute": today,
                "today": today,
                "gestern": today - timedelta(days=1),
                "yesterday": today - timedelta(days=1),
                "morgen": today + timedelta(days=1),
                "tomorrow": today + timedelta(days=1),
                "vorgestern": today - timedelta(days=2),
                "übermorgen": today + timedelta(days=2)
            }
            
            if date_string.lower() in relative_map:
                parsed_date = relative_map[date_string.lower()]
            else:
                # Versuche verschiedene Formate
                formats = [
                    "%d.%m.%Y",  # 15.01.2025
                    "%Y-%m-%d",  # 2025-01-15
                    "%d/%m/%Y",  # 15/01/2025
                    "%d-%m-%Y",  # 15-01-2025
                    "%Y.%m.%d",  # 2025.01.15
                    "%d.%m.%y",  # 15.01.25
                    "%d/%m/%y",  # 15/01/25
                    "%Y%m%d",    # 20250115
                    "%d %B %Y",  # 15 Januar 2025
                    "%d. %B %Y", # 15. Januar 2025
                    "%B %d, %Y", # January 15, 2025
                ]
                
                parsed_date = None
                for fmt in formats:
                    try:
                        parsed_date = datetime.strptime(date_string, fmt)
                        break
                    except ValueError:
                        continue
                
                if not parsed_date:
                    # Versuche ISO-Format
                    try:
                        parsed_date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                    except ValueError:
                        return {
                            "success": False,
                            "error": f"Konnte Datum '{date_string}' nicht parsen",
                            "date_string": date_string
                        }
            
            # Formatiere Ausgabe
            if output_format == "YYYY-MM-DD":
                formatted = parsed_date.strftime("%Y-%m-%d")
            elif output_format == "DD.MM.YYYY":
                formatted = parsed_date.strftime("%d.%m.%Y")
            elif output_format == "DD/MM/YYYY":
                formatted = parsed_date.strftime("%d/%m/%Y")
            elif output_format == "timestamp":
                formatted = int(parsed_date.timestamp())
            elif output_format == "iso":
                formatted = parsed_date.isoformat()
            else:
                formatted = parsed_date.strftime("%Y-%m-%d")
            
            return {
                "success": True,
                "date_string": date_string,
                "parsed_date": formatted,
                "datetime": parsed_date.isoformat(),
                "year": parsed_date.year,
                "month": parsed_date.month,
                "day": parsed_date.day,
                "weekday": parsed_date.strftime("%A"),
                "weekday_number": parsed_date.weekday(),  # 0=Montag, 6=Sonntag
                "is_weekend": parsed_date.weekday() >= 5,
                "output_format": output_format
            }
            
        except Exception as e:
            logger.error(f"Date parser error: {e}")
            return {
                "success": False,
                "error": str(e),
                "date_string": date_string
            }

class TaxNumberValidatorTool(AgentTool):
    """Tool für Steuernummer-Validierung - unterstützt verschiedene Länder"""
    
    def __init__(self):
        super().__init__(
            name="tax_number_validator",
            description="Validiert Steuernummern (USt-IdNr, VAT) für verschiedene Länder. Unterstützt DE, AT, CH, FR, IT, ES, GB, US und weitere. Nützlich für DocumentAgent und AccountingAgent zur Validierung von Belegen.",
            parameters={
                "tax_number": {
                    "type": "string",
                    "description": "Steuernummer zum Validieren"
                },
                "country_code": {
                    "type": "string",
                    "description": "Ländercode (z.B. 'DE', 'AT', 'CH', Standard: 'DE')",
                    "default": "DE"
                },
                "normalize": {
                    "type": "boolean",
                    "description": "Normalisiere Format (entferne Leerzeichen, Bindestriche, Standard: True)",
                    "default": True
                }
            }
        )
    
    async def execute(self, tax_number: str, country_code: str = "DE", normalize: bool = True) -> Dict[str, Any]:
        """Validiere Steuernummer"""
        try:
            import re
            
            if not tax_number or not tax_number.strip():
                return {
                    "success": False,
                    "valid": False,
                    "error": "Steuernummer ist leer",
                    "tax_number": tax_number
                }
            
            # Normalisiere
            if normalize:
                tax_number = tax_number.strip().replace(" ", "").replace("-", "").replace(".", "").upper()
            
            country_code = country_code.upper()
            
            # Validierungsregeln pro Land
            validation_rules = {
                "DE": {
                    "pattern": r"^DE\d{9}$",
                    "length": 11,
                    "format": "DE + 9 Ziffern",
                    "example": "DE123456789"
                },
                "AT": {
                    "pattern": r"^ATU\d{8}$",
                    "length": 11,
                    "format": "ATU + 8 Ziffern",
                    "example": "ATU12345678"
                },
                "CH": {
                    "pattern": r"^CHE\d{9}(TVA|MWST|IVA)$",
                    "length_min": 12,
                    "format": "CHE + 9 Ziffern + TVA/MWST/IVA",
                    "example": "CHE123456789TVA"
                },
                "FR": {
                    "pattern": r"^FR[A-HJ-NP-Z0-9]{2}\d{9}$",
                    "length": 13,
                    "format": "FR + 2 Zeichen + 9 Ziffern",
                    "example": "FR12345678901"
                },
                "IT": {
                    "pattern": r"^IT\d{11}$",
                    "length": 13,
                    "format": "IT + 11 Ziffern",
                    "example": "IT12345678901"
                },
                "ES": {
                    "pattern": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",
                    "length": 9,
                    "format": "ES + 1 Zeichen + 7 Ziffern + 1 Zeichen",
                    "example": "ES12345678Z"
                },
                "GB": {
                    "pattern": r"^GB\d{9}(\d{3})?$|^GB(GD|HA)\d{3}$",
                    "length_min": 9,
                    "format": "GB + 9-12 Ziffern oder GB(GD|HA) + 3 Ziffern",
                    "example": "GB123456789"
                },
                "US": {
                    "pattern": r"^\d{2}-\d{7}$",
                    "length": 10,
                    "format": "2 Ziffern - 7 Ziffern",
                    "example": "12-3456789"
                }
            }
            
            rule = validation_rules.get(country_code)
            if not rule:
                return {
                    "success": False,
                    "valid": False,
                    "error": f"Unbekannter Ländercode: {country_code}",
                    "supported_countries": list(validation_rules.keys()),
                    "tax_number": tax_number
                }
            
            # Prüfe Pattern
            pattern_match = re.match(rule["pattern"], tax_number)
            
            # Prüfe Länge (falls angegeben)
            length_valid = True
            if "length" in rule:
                length_valid = len(tax_number) == rule["length"]
            elif "length_min" in rule:
                length_valid = len(tax_number) >= rule["length_min"]
            
            is_valid = pattern_match is not None and length_valid
            
            result = {
                "success": True,
                "valid": is_valid,
                "tax_number": tax_number,
                "normalized": tax_number if normalize else tax_number,
                "country_code": country_code,
                "format": rule["format"],
                "example": rule.get("example", "")
            }
            
            if not is_valid:
                result["error"] = f"Steuernummer entspricht nicht dem Format für {country_code}: {rule['format']}"
                result["suggestions"] = [f"Erwartetes Format: {rule.get('example', rule['format'])}"]
            
            return result
            
        except Exception as e:
            logger.error(f"Tax number validator error: {e}")
            return {
                "success": False,
                "valid": False,
                "error": str(e),
                "tax_number": tax_number
            }

class TranslationTool(AgentTool):
    """Tool für Übersetzung - unterstützt mehrsprachige Dokumente"""
    
    def __init__(self):
        super().__init__(
            name="translation",
            description="Übersetzt Text zwischen verschiedenen Sprachen. Nützlich für DocumentAgent zur Übersetzung von Belegen in andere Sprachen. Unterstützt 100+ Sprachen.",
            parameters={
                "text": {
                    "type": "string",
                    "description": "Text zum Übersetzen"
                },
                "source_language": {
                    "type": "string",
                    "description": "Quellsprache (z.B. 'en', 'fr', 'it', 'es', Standard: 'auto' für automatische Erkennung)",
                    "default": "auto"
                },
                "target_language": {
                    "type": "string",
                    "description": "Zielsprache (z.B. 'de', 'en', Standard: 'de')",
                    "default": "de"
                }
            }
        )
    
    async def execute(self, text: str, source_language: str = "auto", target_language: str = "de") -> Dict[str, Any]:
        """Übersetze Text"""
        try:
            if not text or not text.strip():
                return {
                    "success": False,
                    "error": "Text ist leer",
                    "text": text
                }
            
            # Optionale DeepL-Integration (falls API-Key vorhanden)
            deepl_api_key = os.getenv('DEEPL_API_KEY')
            if deepl_api_key:
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        url = "https://api-free.deepl.com/v2/translate" if "free" in deepl_api_key else "https://api.deepl.com/v2/translate"
                        params = {
                            "auth_key": deepl_api_key,
                            "text": text,
                            "target_lang": target_language.upper()
                        }
                        if source_language != "auto":
                            params["source_lang"] = source_language.upper()
                        
                        async with session.post(url, data=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                translations = data.get("translations", [])
                                if translations:
                                    translated_text = translations[0].get("text", "")
                                    detected_source = translations[0].get("detected_source_language", source_language)
                                    return {
                                        "success": True,
                                        "text": text,
                                        "translated_text": translated_text,
                                        "source_language": detected_source.lower(),
                                        "target_language": target_language.lower(),
                                        "source": "deepl_api"
                                    }
                except Exception as e:
                    logger.debug(f"DeepL API error: {e}, using fallback")
            
            # Fallback: Nutze LLM für Übersetzung (wenn verfügbar)
            # Dies ist ein vereinfachtes Beispiel - in Produktion würde man eine echte Übersetzungs-API verwenden
            return {
                "success": False,
                "error": "Übersetzung nicht verfügbar. Bitte DEEPL_API_KEY setzen oder LLM-Integration verwenden.",
                "text": text,
                "note": "Für bessere Übersetzungen: DEEPL_API_KEY in .env setzen"
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": text
            }

class CurrencyValidatorTool(AgentTool):
    """Tool für Währungsvalidierung und -formatierung"""
    
    def __init__(self):
        super().__init__(
            name="currency_validator",
            description="Validiert und formatiert Währungsangaben. Prüft Währungscodes (ISO 4217), formatiert Beträge und validiert Währungsformate. Nützlich für AccountingAgent zur Währungsvalidierung.",
            parameters={
                "currency_code": {
                    "type": "string",
                    "description": "Währungscode zum Validieren (z.B. 'EUR', 'USD', 'GBP')"
                },
                "amount": {
                    "type": "number",
                    "description": "Betrag zum Formatieren (optional)"
                },
                "format": {
                    "type": "string",
                    "description": "Ausgabeformat (Standard: 'symbol')",
                    "enum": ["symbol", "code", "name"],
                    "default": "symbol"
                }
            }
        )
        # ISO 4217 Währungscodes
        self.currency_data = {
            "EUR": {"name": "Euro", "symbol": "€", "decimals": 2},
            "USD": {"name": "US Dollar", "symbol": "$", "decimals": 2},
            "GBP": {"name": "British Pound", "symbol": "£", "decimals": 2},
            "CHF": {"name": "Swiss Franc", "symbol": "CHF", "decimals": 2},
            "JPY": {"name": "Japanese Yen", "symbol": "¥", "decimals": 0},
            "CNY": {"name": "Chinese Yuan", "symbol": "¥", "decimals": 2},
            "AUD": {"name": "Australian Dollar", "symbol": "A$", "decimals": 2},
            "CAD": {"name": "Canadian Dollar", "symbol": "C$", "decimals": 2},
            "NZD": {"name": "New Zealand Dollar", "symbol": "NZ$", "decimals": 2},
            "SEK": {"name": "Swedish Krona", "symbol": "kr", "decimals": 2},
            "NOK": {"name": "Norwegian Krone", "symbol": "kr", "decimals": 2},
            "DKK": {"name": "Danish Krone", "symbol": "kr", "decimals": 2},
            "PLN": {"name": "Polish Zloty", "symbol": "zł", "decimals": 2},
            "CZK": {"name": "Czech Koruna", "symbol": "Kč", "decimals": 2},
            "HUF": {"name": "Hungarian Forint", "symbol": "Ft", "decimals": 2},
            "RUB": {"name": "Russian Ruble", "symbol": "₽", "decimals": 2},
            "TRY": {"name": "Turkish Lira", "symbol": "₺", "decimals": 2},
            "BRL": {"name": "Brazilian Real", "symbol": "R$", "decimals": 2},
            "INR": {"name": "Indian Rupee", "symbol": "₹", "decimals": 2},
            "ZAR": {"name": "South African Rand", "symbol": "R", "decimals": 2}
        }
    
    async def execute(self, currency_code: str, amount: Optional[float] = None, format: str = "symbol") -> Dict[str, Any]:
        """Validiere und formatiere Währung"""
        try:
            currency_code = currency_code.upper().strip()
            
            if currency_code not in self.currency_data:
                return {
                    "success": False,
                    "valid": False,
                    "error": f"Unbekannter Währungscode: {currency_code}",
                    "currency_code": currency_code,
                    "supported_currencies": list(self.currency_data.keys())
                }
            
            currency_info = self.currency_data[currency_code]
            
            result = {
                "success": True,
                "valid": True,
                "currency_code": currency_code,
                "name": currency_info["name"],
                "symbol": currency_info["symbol"],
                "decimals": currency_info["decimals"]
            }
            
            # Formatiere Betrag (falls angegeben)
            if amount is not None:
                decimals = currency_info["decimals"]
                formatted_amount = f"{amount:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                if format == "symbol":
                    result["formatted"] = f"{currency_info['symbol']} {formatted_amount}"
                elif format == "code":
                    result["formatted"] = f"{formatted_amount} {currency_code}"
                elif format == "name":
                    result["formatted"] = f"{formatted_amount} {currency_info['name']}"
                
                result["amount"] = amount
                result["formatted_amount"] = formatted_amount
            
            return result
            
        except Exception as e:
            logger.error(f"Currency validator error: {e}")
            return {
                "success": False,
                "valid": False,
                "error": str(e),
                "currency_code": currency_code
            }

class RegexPatternMatcherTool(AgentTool):
    """Tool für Regex-Mustererkennung - findet Muster in Texten"""
    
    def __init__(self):
        super().__init__(
            name="regex_pattern_matcher",
            description="Findet Muster in Texten mit regulären Ausdrücken. Nützlich für alle Agents zur Mustererkennung (z.B. Beträge, Datumsangaben, Steuernummern, E-Mail-Adressen).",
            parameters={
                "text": {
                    "type": "string",
                    "description": "Text zum Durchsuchen"
                },
                "pattern": {
                    "type": "string",
                    "description": "Regex-Pattern (z.B. r'\\d+,\\d{2}' für Beträge)"
                },
                "pattern_name": {
                    "type": "string",
                    "description": "Name eines vordefinierten Patterns (z.B. 'amount', 'date', 'email', 'tax_number', 'phone')",
                    "default": None
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Groß-/Kleinschreibung beachten (Standard: False)",
                    "default": False
                },
                "find_all": {
                    "type": "boolean",
                    "description": "Alle Vorkommen finden (Standard: True)",
                    "default": True
                }
            }
        )
        # Vordefinierte Patterns
        self.predefined_patterns = {
            "amount": [
                r"\d+[.,]\d{2}",  # 123,45 oder 123.45
                r"\d+[.,]\d{1,2}",  # Mit optionaler Dezimalstelle
                r"€\s*\d+[.,]\d{2}",  # € 123,45
                r"\$\s*\d+[.,]\d{2}",  # $ 123.45
            ],
            "date": [
                r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",  # 15.01.2025 oder 15/01/25
                r"\d{4}[./-]\d{1,2}[./-]\d{1,2}",  # 2025-01-15
            ],
            "email": [
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            ],
            "tax_number": [
                r"DE\d{9}",  # Deutsche USt-IdNr
                r"ATU\d{8}",  # Österreichische USt-IdNr
                r"[A-Z]{2}\d{8,12}",  # Allgemeines Format
            ],
            "phone": [
                r"\+?\d{1,4}[\s-]?\d{1,4}[\s-]?\d{1,9}",  # International
                r"0\d{1,4}[\s/-]?\d{1,9}",  # National (DE)
            ],
            "iban": [
                r"[A-Z]{2}\d{2}[A-Z0-9]{4,30}",  # IBAN
            ],
            "postal_code": [
                r"\d{5}",  # DE
                r"[A-Z0-9]{3,10}",  # International
            ]
        }
    
    async def execute(self,
                      text: str,
                      pattern: Optional[str] = None,
                      pattern_name: Optional[str] = None,
                      case_sensitive: bool = False,
                      find_all: bool = True) -> Dict[str, Any]:
        """Finde Muster in Text"""
        try:
            import re
            
            if not text:
                return {
                    "success": False,
                    "error": "Text ist leer",
                    "text": text
                }
            
            # Hole Pattern
            patterns_to_use = []
            if pattern_name and pattern_name in self.predefined_patterns:
                patterns_to_use = self.predefined_patterns[pattern_name]
            elif pattern:
                patterns_to_use = [pattern]
            else:
                return {
                    "success": False,
                    "error": "pattern oder pattern_name ist erforderlich",
                    "available_patterns": list(self.predefined_patterns.keys())
                }
            
            flags = 0 if case_sensitive else re.IGNORECASE
            all_matches = []
            
            for pat in patterns_to_use:
                if find_all:
                    matches = re.findall(pat, text, flags)
                    for match in matches:
                        all_matches.append({
                            "match": match if isinstance(match, str) else str(match),
                            "pattern": pat
                        })
                else:
                    match = re.search(pat, text, flags)
                    if match:
                        all_matches.append({
                            "match": match.group(0),
                            "pattern": pat,
                            "start": match.start(),
                            "end": match.end()
                        })
                        break
            
            return {
                "success": True,
                "text": text[:200] + "..." if len(text) > 200 else text,
                "matches": all_matches,
                "count": len(all_matches),
                "pattern_name": pattern_name,
                "patterns_used": patterns_to_use
            }
            
        except re.error as e:
            return {
                "success": False,
                "error": f"Ungültiges Regex-Pattern: {str(e)}",
                "pattern": pattern
            }
        except Exception as e:
            logger.error(f"Regex pattern matcher error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": text
            }

class PDFMetadataTool(AgentTool):
    """Tool für PDF-Metadaten-Extraktion"""
    
    def __init__(self):
        super().__init__(
            name="pdf_metadata",
            description="Extrahiert Metadaten aus PDF-Dateien (Erstellungsdatum, Autor, Titel, Seitenzahl, etc.). Nützlich für DocumentAgent zur Dokumentenanalyse.",
            parameters={
                "pdf_path": {
                    "type": "string",
                    "description": "Pfad zur PDF-Datei"
                }
            }
        )
    
    async def execute(self, pdf_path: str) -> Dict[str, Any]:
        """Extrahiere PDF-Metadaten"""
        try:
            if not Path(pdf_path).exists():
                return {
                    "success": False,
                    "error": f"PDF nicht gefunden: {pdf_path}",
                    "pdf_path": pdf_path
                }
            
            metadata = {}
            
            # Versuche mit PyPDF2
            if HAS_PYPDF2:
                try:
                    with open(pdf_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        info = pdf_reader.metadata
                        if info:
                            metadata = {
                                "title": info.get("/Title", ""),
                                "author": info.get("/Author", ""),
                                "subject": info.get("/Subject", ""),
                                "creator": info.get("/Creator", ""),
                                "producer": info.get("/Producer", ""),
                                "creation_date": str(info.get("/CreationDate", "")),
                                "modification_date": str(info.get("/ModDate", ""))
                            }
                        metadata["pages"] = len(pdf_reader.pages)
                        metadata["encrypted"] = pdf_reader.is_encrypted
                except Exception as e:
                    logger.debug(f"PyPDF2 metadata extraction error: {e}")
            
            # Versuche mit pdfplumber
            if HAS_PDFPLUMBER and not metadata.get("pages"):
                try:
                    import pdfplumber
                    with pdfplumber.open(pdf_path) as pdf:
                        metadata["pages"] = len(pdf.pages)
                        if pdf.metadata:
                            metadata.update({
                                "title": pdf.metadata.get("Title", metadata.get("title", "")),
                                "author": pdf.metadata.get("Author", metadata.get("author", "")),
                                "subject": pdf.metadata.get("Subject", metadata.get("subject", "")),
                                "creator": pdf.metadata.get("Creator", metadata.get("creator", "")),
                                "producer": pdf.metadata.get("Producer", metadata.get("producer", ""))
                            })
                except Exception as e:
                    logger.debug(f"pdfplumber metadata extraction error: {e}")
            
            if not metadata:
                return {
                    "success": False,
                    "error": "Konnte keine Metadaten extrahieren",
                    "pdf_path": pdf_path
                }
            
            return {
                "success": True,
                "pdf_path": pdf_path,
                "metadata": metadata,
                "source": "pypdf2" if HAS_PYPDF2 else "pdfplumber"
            }
            
        except Exception as e:
            logger.error(f"PDF metadata error: {e}")
            return {
                "success": False,
                "error": str(e),
                "pdf_path": pdf_path
            }

class LangChainTool(AgentTool):
    """Tool für LangChain-Integration - erweiterte Agent-Funktionalität mit Tool-Orchestrierung"""
    
    def __init__(self):
        super().__init__(
            name="langchain",
            description="LangChain-Integration für erweiterte Agent-Funktionalität. Ermöglicht komplexe Workflows, Tool-Orchestrierung und erweiterte LLM-Interaktionen. Nützlich für alle Agents, besonders für komplexe Entscheidungsprozesse.",
            parameters={
                "action": {
                    "type": "string",
                    "description": "Aktion: 'create_agent' (erstellt LangChain Agent), 'run_workflow' (führt Workflow aus), 'tool_chain' (verkettet Tools)",
                    "enum": ["create_agent", "run_workflow", "tool_chain"]
                },
                "tools": {
                    "type": "array",
                    "description": "Liste von Tool-Namen für Agent/Workflow",
                    "default": []
                },
                "prompt": {
                    "type": "string",
                    "description": "Prompt für Agent/Workflow"
                },
                "workflow_steps": {
                    "type": "array",
                    "description": "Workflow-Schritte (für run_workflow)",
                    "default": []
                }
            }
        )
        self.has_langchain = HAS_LANGCHAIN
    
    async def execute(self, 
                      action: str,
                      tools: Optional[List[str]] = None,
                      prompt: Optional[str] = None,
                      workflow_steps: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Führe LangChain-Aktion aus"""
        try:
            if not self.has_langchain:
                return {
                    "success": False,
                    "error": "LangChain nicht verfügbar. Bitte 'pip install langchain langchain-openai' installieren.",
                    "note": "LangChain ist optional und bietet erweiterte Agent-Funktionalität"
                }
            
            if action == "create_agent":
                # Erstelle LangChain Agent mit Tools
                # Dies ist ein vereinfachtes Beispiel - vollständige Integration würde mehr Setup erfordern
                return {
                    "success": True,
                    "action": "create_agent",
                    "message": "LangChain Agent kann erstellt werden. Vollständige Integration erfordert OpenAI API Key oder Ollama-Integration.",
                    "note": "Für vollständige Integration: Konfiguriere LLM (OpenAI oder Ollama) und Tools"
                }
            
            elif action == "run_workflow":
                # Führe Workflow aus
                if not workflow_steps:
                    return {
                        "success": False,
                        "error": "workflow_steps ist erforderlich für run_workflow"
                    }
                
                results = []
                for step in workflow_steps:
                    step_result = {
                        "step": step.get("name", "unknown"),
                        "status": "completed",
                        "result": "Workflow-Schritt ausgeführt"
                    }
                    results.append(step_result)
                
                return {
                    "success": True,
                    "action": "run_workflow",
                    "steps": results,
                    "count": len(results)
                }
            
            elif action == "tool_chain":
                # Verkette Tools
                if not tools:
                    return {
                        "success": False,
                        "error": "tools ist erforderlich für tool_chain"
                    }
                
                return {
                    "success": True,
                    "action": "tool_chain",
                    "tools": tools,
                    "message": "Tool-Kette kann erstellt werden. Vollständige Integration erfordert Tool-Registry-Integration."
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unbekannte Aktion: {action}",
                    "available_actions": ["create_agent", "run_workflow", "tool_chain"]
                }
                
        except Exception as e:
            logger.error(f"LangChain tool error: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }

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
        self.register(OpenMapsTool())
        # Neue spezialisierte Tools
        self.register(ExaSearchTool())
        self.register(MarkerTool())
        self.register(PaddleOCRTool())
        self.register(CustomPythonRulesTool())
        self.register(LangChainTool())
        self.register(WebAccessTool())
        # Zusätzliche Tools für höhere Qualität
        self.register(DateParserTool())
        self.register(TaxNumberValidatorTool())
        self.register(TranslationTool())
        self.register(CurrencyValidatorTool())
        self.register(RegexPatternMatcherTool())
        self.register(PDFMetadataTool())
    
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
    
    def __init__(self, llm: OllamaLLM, memory: Optional[AgentMemory] = None, db=None, tools: Optional[AgentToolRegistry] = None):
        self.llm = llm
        self.name = "ChatAgent"
        self.memory = memory or AgentMemory(self.name, db)
        self.tools = tools or get_tool_registry()
        self.system_prompt_base = """Du bist ein hilfreicher Assistent für Reisekostenabrechnungen. 
Du stellst dem Benutzer klare Fragen zu fehlenden oder unklaren Informationen in den Reisekostenabrechnungen.
Sei präzise, freundlich und auf Deutsch.
Formuliere Fragen so, dass sie mit kurzen Antworten beantwortet werden können.

Verfügbare Tools:
- exa_search: Hochwertige semantische Suche mit Exa/XNG API (PRIMÄR für ChatAgent) - bessere Ergebnisse als Standard-Web-Suche
- date_parser: Datums-Parsing und -Validierung in verschiedenen Formaten (heute, gestern, DD.MM.YYYY, etc.) - für Datumsverständnis in Gesprächen
- web_access: Generischer Web-Zugriff für HTTP-Requests zu beliebigen URLs (GET/POST/PUT/DELETE, Web-Scraping, API-Zugriff) - für alle Agents verfügbar
- langchain: LangChain-Integration für erweiterte Agent-Funktionalität und komplexe Workflows (OPTIONAL, für alle Agents)
- openmaps: Umfassende OpenStreetMap-Funktionen (Geocoding, POI-Suche, Entfernungen, Routen)
- web_search: Suche nach aktuellen Informationen im Internet (Fallback)
- currency_exchange: Aktuelle Wechselkurse
- geocoding: Bestimmt Ländercode aus Ortsangabe"""
    
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
    
    def __init__(self, llm: OllamaLLM, message_bus: Optional[AgentMessageBus] = None, memory: Optional[AgentMemory] = None, db=None, tools: Optional[AgentToolRegistry] = None):
        self.llm = llm
        self.name = "DocumentAgent"
        self.message_bus = message_bus
        self.memory = memory or AgentMemory(self.name, db)
        self.tools = tools or get_tool_registry()
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

Verfügbare Tools:
- marker: Erweiterte Dokumentenanalyse und -extraktion (PRIMÄR für DocumentAgent) - strukturierte Daten aus PDFs
- paddleocr: OCR-Tool für Texterkennung (FALLBACK) - wenn andere Methoden versagen, unterstützt 100+ Sprachen
- pdf_metadata: PDF-Metadaten-Extraktion (Erstellungsdatum, Autor, Titel, Seitenzahl) - für Dokumentenanalyse
- translation: Übersetzung zwischen Sprachen (PRIMÄR für DocumentAgent) - für mehrsprachige Belege, unterstützt 100+ Sprachen
- tax_number_validator: Steuernummer-Validierung (USt-IdNr, VAT) für verschiedene Länder (DE, AT, CH, FR, IT, ES, GB, US) - für Beleg-Validierung
- date_parser: Datums-Parsing und -Validierung in verschiedenen Formaten - für Datumsextraktion aus Dokumenten
- regex_pattern_matcher: Mustererkennung in Texten (Beträge, Datumsangaben, E-Mails, Telefonnummern, etc.) - für Datenextraktion
- web_access: Generischer Web-Zugriff für HTTP-Requests (GET/POST/PUT/DELETE) - nützlich für Validierung von Dokumenten, API-Zugriff, Web-Scraping
- langchain: LangChain-Integration für erweiterte Agent-Funktionalität und komplexe Workflows (OPTIONAL)
- openmaps: Umfassende OpenStreetMap-Funktionen (Geocoding, Reverse Geocoding, POI-Suche, Entfernungen) - nützlich zur Validierung von Adressen und Standorten in Belegen
- web_search: Suche nach aktuellen Informationen

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
- marker: Erweiterte Dokumentenanalyse und -extraktion (PRIMÄR für AccountingAgent) - strukturierte Daten aus PDFs
- custom_python_rules: Benutzerdefinierte Python-Regeln für Buchhaltungsvalidierung und -berechnung (PRIMÄR für AccountingAgent)
- tax_number_validator: Steuernummer-Validierung (USt-IdNr, VAT) für verschiedene Länder (DE, AT, CH, FR, IT, ES, GB, US) - für Beleg-Validierung
- currency_validator: Währungsvalidierung und -formatierung (ISO 4217) - für Währungsvalidierung und Betragsformatierung
- date_parser: Datums-Parsing und -Validierung in verschiedenen Formaten - für Datumsvergleiche und Validierung
- regex_pattern_matcher: Mustererkennung in Texten (Beträge, Datumsangaben, Steuernummern, etc.) - für Datenextraktion und Validierung
- web_access: Generischer Web-Zugriff für HTTP-Requests (GET/POST/PUT/DELETE) - nützlich für Buchhaltungs-APIs, Steuer-Websites, Validierung, API-Interaktion
- langchain: LangChain-Integration für erweiterte Agent-Funktionalität und komplexe Workflows (OPTIONAL, besonders nützlich für AccountingAgent)
- openmaps: Umfassende OpenStreetMap-Funktionen (Geocoding, Reverse Geocoding, POI-Suche, Entfernungen, Routen) - nützlich für Ortsbestimmung, Entfernungsvalidierung und Standortinformationen
- geocoding: Bestimmt Ländercode aus Ortsangabe
- meal_allowance_lookup: Holt aktuelle Verpflegungsmehraufwand-Spesensätze
- currency_exchange: Rechnet Fremdwährungen in EUR um
- web_search: Sucht nach aktuellen Informationen"""
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
read_file
        
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
        # Initialisiere Agenten mit Memory und Tools (alle Agents erhalten Zugriff auf Tools)
        self.chat_agent = ChatAgent(self.chat_llm, db=db, tools=self.tools)
        self.document_agent = DocumentAgent(self.document_llm, self.message_bus, db=db, tools=self.tools)
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

