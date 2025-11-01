"""
Autogen Agent Network for Travel Expense Report Review
Implements specialized agents: Chat Agent, Document Agent, Accounting Agent
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
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

# Ollama configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

# Prompt directory
PROMPTS_DIR = Path(__file__).parent / "prompts"

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

class OllamaLLM:
    """Wrapper for Ollama LLM API"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model
    
    async def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        """Send chat messages to Ollama and get response"""
        try:
            # Prepare messages with system prompt
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            formatted_messages.extend(messages)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": formatted_messages,
                        "stream": False
                    },
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("message", {}).get("content", "")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {response.status} - {error_text}")
                        return f"Fehler bei LLM-Anfrage: {response.status}"
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return f"Fehler bei Kommunikation mit LLM: {str(e)}"
    
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
    
    def __init__(self, llm: OllamaLLM):
        self.llm = llm
        self.name = "ChatAgent"
        self.system_prompt = """Du bist ein hilfreicher Assistent für Reisekostenabrechnungen. 
Du stellst dem Benutzer klare Fragen zu fehlenden oder unklaren Informationen in den Reisekostenabrechnungen.
Sei präzise, freundlich und auf Deutsch.
Formuliere Fragen so, dass sie mit kurzen Antworten beantwortet werden können."""
    
    async def process(self, context: Dict[str, Any], user_message: Optional[str] = None) -> AgentResponse:
        """Process user message or generate question based on context"""
        report_issues = context.get("issues", [])
        missing_info = context.get("missing_info", [])
        
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
            ], self.system_prompt)
            
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
                ], self.system_prompt)
            else:
                response_text = "Alle Informationen sind vollständig. Die Prüfung kann fortgesetzt werden."
            
            return AgentResponse(
                agent_name=self.name,
                message=response_text,
                requires_user_input=len(missing_info) > 0
            )

class DocumentAgent:
    """Agent für Dokumentenanalyse: Verstehen, Übersetzen, Kategorisieren, Validieren"""
    
    def __init__(self, llm: OllamaLLM, message_bus: Optional[AgentMessageBus] = None):
        self.llm = llm
        self.name = "DocumentAgent"
        self.message_bus = message_bus
        # Load prompt from markdown file
        self.system_prompt = load_prompt("document_agent.md")
        if not self.system_prompt:
            # Fallback default prompt
            self.system_prompt = """Du bist ein Experte für Dokumentenanalyse von Reisekostenbelegen.
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
    
    def handle_agent_message(self, message: Dict):
        """Handle messages from other agents"""
        logger.info(f"DocumentAgent received message from {message.get('from')}: {message.get('content')}")
        # Can request clarification from Chat Agent if needed
        if message.get('from') == 'ChatAgent':
            # Chat Agent might request document re-analysis
            pass
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        extracted_text = ""
        
        try:
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
        except Exception as e:
            logger.warning(f"Could not extract text from PDF {pdf_path}: {e}")
        
        return extracted_text
    
    async def analyze_document(self, receipt_path: str, filename: str) -> DocumentAnalysis:
        """Analyze a PDF receipt document"""
        try:
            # Extract text from PDF
            pdf_text = self.extract_pdf_text(receipt_path)
            
            # Limit text length for LLM (first 5000 characters)
            pdf_text_limited = pdf_text[:5000] if pdf_text else "Kein Text extrahiert"
            
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
            
            analysis_json = await self.llm.extract_json(prompt, self.system_prompt)
            
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
            return DocumentAnalysis(
                document_type=analysis_json.get("document_type", "unknown"),
                language=analysis_json.get("language", "de"),
                translated_content=analysis_json.get("translated_content"),
                extracted_data=analysis_json.get("extracted_data", {}),
                validation_issues=analysis_json.get("validation_issues", []),
                completeness_check=analysis_json.get("completeness_check", {}),
                confidence=float(analysis_json.get("confidence", 0.5))
            )
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
    
    async def process(self, receipts: List[Dict[str, Any]]) -> List[DocumentAnalysis]:
        """Process multiple receipts"""
        analyses = []
        for receipt in receipts:
            analysis = await self.analyze_document(
                receipt.get("local_path", ""),
                receipt.get("filename", "")
            )
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
    
    def __init__(self, llm: OllamaLLM, message_bus: Optional[AgentMessageBus] = None):
        self.llm = llm
        self.name = "AccountingAgent"
        self.message_bus = message_bus
        # Load prompt from markdown file
        self.system_prompt = load_prompt("accounting_agent.md")
        if not self.system_prompt:
            # Fallback default prompt
            self.system_prompt = """Du bist ein Buchhaltungs-Experte für Reisekostenabrechnungen.
Deine Aufgaben:
1. Dokumente den Reisekosteneinträgen zuordnen (basierend auf Datum, Ort, Zweck)
2. Verpflegungsmehraufwand automatisch berechnen (basierend auf Land und Abwesenheitsdauer)
3. Spezielle Dokumente zuordnen (Maut, Parken, etc.)
4. Kategorien korrekt zuweisen
5. Beträge validieren und korrigieren"""
        
        # Subscribe to messages from other agents
        if self.message_bus:
            self.message_bus.subscribe(self.name, self.handle_agent_message)
    
    def handle_agent_message(self, message: Dict):
        """Handle messages from other agents"""
        logger.info(f"AccountingAgent received message from {message.get('from')}: {message.get('content')}")
        # Can request document analysis from Document Agent or clarification from Chat Agent
    
    def get_country_code(self, location: str) -> str:
        """Get country code from location (simplified - would use geocoding API)"""
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
    
    def get_meal_allowance(self, location: str, days: int, is_24h_absence: bool = True) -> float:
        """Get Verpflegungsmehraufwand based on location and duration"""
        country_code = self.get_country_code(location)
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
                
                match_result = await self.llm.extract_json(prompt, self.system_prompt)
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
                    meal_allowance = self.get_meal_allowance(location, days, is_24h_absence=True)
                
                assignments.append(ExpenseAssignment(
                    receipt_id=receipt.get("id", ""),
                    entry_date=matching_entry.get("date", ""),
                    category=category,
                    amount=doc_amount,
                    currency=analysis.extracted_data.get("currency", "EUR"),
                    meal_allowance_added=meal_allowance,
                    assignment_confidence=analysis.confidence
                ))
        
        return assignments
    
    async def process(self, report: Dict, document_analyses: List[DocumentAnalysis]) -> Dict[str, Any]:
        """Process expense assignment and meal allowance"""
        report_entries = report.get("entries", [])
        assignments = await self.assign_expenses(
            report_entries,
            document_analyses,
            report.get("receipts", [])
        )
        
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
                meal_allowance = self.get_meal_allowance(location, days, is_24h_absence=True)
                total_meal_allowance += meal_allowance
        
        return {
            "assignments": [a.model_dump() for a in assignments],
            "total_expenses": round(total_expenses, 2),
            "total_meal_allowance": round(total_meal_allowance, 2),
            "summary": f"Zuordnung abgeschlossen: {len(assignments)} Dokumente zugeordnet, Gesamtausgaben: {total_expenses:.2f} EUR, Verpflegungsmehraufwand: {total_meal_allowance:.2f} EUR"
        }

class AgentOrchestrator:
    """Orchestrates the agent network for expense report review"""
    
    def __init__(self):
        self.llm = OllamaLLM()
        self.chat_agent = ChatAgent(self.llm)
        self.document_agent = DocumentAgent(self.llm)
        self.accounting_agent = AccountingAgent(self.llm)
    
    async def review_expense_report(self, report_id: str, db) -> Dict[str, Any]:
        """Main orchestration method for reviewing an expense report"""
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

