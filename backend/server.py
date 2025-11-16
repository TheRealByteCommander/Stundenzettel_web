from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Form, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from motor.motor_asyncio import AsyncIOMotorClient
import os
os.environ.setdefault("PASSLIB_DISABLED_HASHES", "bcrypt")
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
import pyotp
from passlib.context import CryptContext
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import json
import re
from pywebpush import webpush, WebPushException

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@schmitz-intralogistik.de").strip().lower()
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "Administrator").strip() or "Administrator"
LEGACY_ADMIN_EMAILS = {
    email.strip().lower()
    for email in os.getenv("LEGACY_ADMIN_EMAILS", "admin@app.byte-commander.de").split(",")
    if email.strip()
}
LEGACY_ADMIN_EMAILS.add(DEFAULT_ADMIN_EMAIL)
TEST_ANNOUNCEMENT_TITLE = os.getenv("TEST_ANNOUNCEMENT_TITLE", "Testsystem-Ankündigung")
TEST_ANNOUNCEMENT_CONTENT = os.getenv(
    "TEST_ANNOUNCEMENT_CONTENT",
    "<p>Dies ist eine automatische Test-Ankündigung, um die Frontend-Anzeige zu verifizieren.</p>"
)

# MongoDB connection
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.getenv('DB_NAME', 'stundenzettel')]

# Local storage path for receipts (on office computer, not webserver)
# DSGVO-Compliance: Dokumente werden nur lokal auf Office-Rechner gespeichert
LOCAL_RECEIPTS_PATH = os.getenv('LOCAL_RECEIPTS_PATH', 'C:/Reisekosten_Belege')

# Validate that storage path is local (not on webserver)
from compliance import validate_local_storage_path, DataEncryption, AuditLogger, RetentionManager, AITransparency
is_valid, error_msg = validate_local_storage_path(LOCAL_RECEIPTS_PATH)
if not is_valid:
    logging.error(f"INVALID STORAGE PATH: {error_msg}")
    logging.error("LOCAL_RECEIPTS_PATH must point to a local office computer, not a webserver!")
    raise ValueError(f"Invalid storage path: {error_msg}")

# Ensure directory exists
if LOCAL_RECEIPTS_PATH and not Path(LOCAL_RECEIPTS_PATH).exists():
    try:
        Path(LOCAL_RECEIPTS_PATH).mkdir(parents=True, exist_ok=True)
        logging.info(f"Created local receipts directory: {LOCAL_RECEIPTS_PATH}")
    except Exception as e:
        logging.error(f"Could not create local receipts directory: {e}")
        raise

# Initialize compliance modules
data_encryption = DataEncryption()  # Will use ENCRYPTION_KEY from env or warn
audit_logger = AuditLogger()
retention_manager = RetentionManager(db)

# Ollama configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://192.168.178.155:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

# JWT and Password settings
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)
security = HTTPBearer()

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Tick Guard - Zeiterfassung & Reisekosten")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api_router = APIRouter(prefix="/api")

# Web Push (VAPID) configuration
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL", "admin@example.com")

class PushSubscription(BaseModel):
    endpoint: str
    keys: Dict[str, str]
    user_id: Optional[str] = None
    role: Optional[str] = None  # optional: 'user' | 'admin' | 'accounting'

async def save_push_subscription(sub: Dict[str, Any]):
    existing = await db.push_subscriptions.find_one({"endpoint": sub.get("endpoint")})
    if existing:
        await db.push_subscriptions.update_one({"endpoint": sub.get("endpoint")}, {"$set": sub})
    else:
        await db.push_subscriptions.insert_one({**sub, "created_at": datetime.utcnow()})

async def delete_push_subscription(endpoint: str):
    await db.push_subscriptions.delete_one({"endpoint": endpoint})

def send_web_push(subscription: Dict[str, Any], payload: Dict[str, Any]):
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        logging.warning("VAPID keys not configured - skipping web push")
        return
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{VAPID_CLAIM_EMAIL}"}
        )
    except WebPushException as e:
        logging.warning(f"WebPush failed: {e}")

async def notify_user(user_id: str, title: str, body: str, data: Optional[Dict[str, Any]] = None):
    async for sub in db.push_subscriptions.find({"user_id": user_id}):
        send_web_push({"endpoint": sub["endpoint"], "keys": sub["keys"]}, {"title": title, "body": body, "data": data or {}})

async def notify_role(role: str, title: str, body: str, data: Optional[Dict[str, Any]] = None):
    async for sub in db.push_subscriptions.find({"role": role}):
        send_web_push({"endpoint": sub["endpoint"], "keys": sub["keys"]}, {"title": title, "body": body, "data": data or {}})

@api_router.get("/push/public-key")
async def get_push_public_key():
    return {"publicKey": VAPID_PUBLIC_KEY}

@api_router.post("/push/subscribe")
async def subscribe_push(subscription: Dict[str, Any], current_user: "User" = Depends(lambda: get_current_user())):
    sub = {
        "endpoint": subscription.get("endpoint"),
        "keys": subscription.get("keys", {}),
        "user_id": current_user.id,
        "role": current_user.role
    }
    await save_push_subscription(sub)
    return {"status": "ok"}

@api_router.post("/push/unsubscribe")
async def unsubscribe_push(endpoint: str, current_user: "User" = Depends(lambda: get_current_user())):
    await delete_push_subscription(endpoint)
    return {"status": "ok"}

# Company Information
COMPANY_INFO = {
    "name": "Byte Commander",
    "address": "",
    "city": "",
    "country": "Deutschland"
}

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    role: str = "user"  # "user", "admin", "accounting"
    hashed_password: str
    two_fa_enabled: bool = False
    two_fa_secret: Optional[str] = None
    weekly_hours: float = 40.0  # Wochenstundenzahl (Standard 40h)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Backward compatibility: is_admin property
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
    
    def can_view_all_data(self) -> bool:
        """Check if user can view all employee data (admin or accounting)"""
        return self.role in ["admin", "accounting"]

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "user"  # "user", "admin", "accounting"
    weekly_hours: float = 40.0  # Wochenstundenzahl
    # Backward compatibility
    is_admin: Optional[bool] = None
    
    def __init__(self, **data):
        # Handle backward compatibility: convert is_admin to role
        if 'is_admin' in data and 'role' not in data:
            data['role'] = "admin" if data.pop('is_admin') else "user"
        # Set default weekly_hours if not provided
        if 'weekly_hours' not in data:
            data['weekly_hours'] = 40.0
        super().__init__(**data)

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    otp: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[str] = None  # "user", "admin", "accounting"
    weekly_hours: Optional[float] = None  # Wochenstundenzahl
    # Backward compatibility
    is_admin: Optional[bool] = None
    
    def __init__(self, **data):
        # Handle backward compatibility: convert is_admin to role
        if 'is_admin' in data and 'role' not in data:
            data['role'] = "admin" if data.pop('is_admin') else "user"
        super().__init__(**data)

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class TwoFAVerify(BaseModel):
    otp: str
    temp_token: Optional[str] = None  # Optional for initial setup endpoint

class TwoFASetupResponse(BaseModel):
    secret: str
    otpauth_uri: str

class MonthlyStatsRequest(BaseModel):
    month: str  # YYYY-MM

class MonthlyUserStat(BaseModel):
    user_id: str
    user_name: str
    month: str
    total_hours: float

class MonthlyStatsResponse(BaseModel):
    month: str
    stats: List[MonthlyUserStat]

class MonthlyRankResponse(BaseModel):
    month: str
    rank: int
    total_users: int

class AccountingMonthlyStat(BaseModel):
    user_id: str
    user_name: str
    month: str
    total_hours: float  # Alle Stunden (inkl. Fahrzeit)
    hours_on_timesheets: float  # Stunden die auf Stundenzetteln erscheinen
    travel_hours: float  # Fahrzeit
    travel_hours_on_timesheets: float  # Fahrzeit die auf Stundenzetteln erscheint (include_travel_time=True)
    travel_kilometers: float = 0.0  # Gesamtkilometer
    travel_expenses: float = 0.0  # Gesamte Reisekosten in Euro
    timesheets_count: int  # Anzahl Stundenzettel

class AccountingStatsResponse(BaseModel):
    month: str
    stats: List[AccountingMonthlyStat]

class TimeEntry(BaseModel):
    date: str  # YYYY-MM-DD format
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    break_minutes: int
    tasks: str
    customer_project: str
    location: str
    absence_type: Optional[str] = None  # "urlaub", "krankheit", "feiertag", or None
    travel_time_minutes: int = 0  # Fahrzeit in Minuten
    include_travel_time: bool = False  # Checkbox "Weiterberechnen"
    vehicle_id: Optional[str] = None  # Zugeordnetes Fahrzeug

class TimesheetUpdate(BaseModel):
    week_start: Optional[str] = None
    week_vehicle_id: Optional[str] = None
    entries: Optional[List[TimeEntry]] = None
    signed_pdf_verification_notes: Optional[str] = None
    signed_pdf_verified: Optional[bool] = None

class WeeklyTimesheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    week_start: str  # Monday date in YYYY-MM-DD format
    week_end: str    # Sunday date in YYYY-MM-DD format
    entries: List[TimeEntry]
    week_vehicle_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "draft"  # draft, sent, approved
    signed_pdf_path: Optional[str] = None  # Pfad zum hochgeladenen unterschriebenen PDF
    signed_pdf_verified: Optional[bool] = False  # Durch Dokumenten-Agent verifiziert
    signed_pdf_verification_notes: Optional[str] = None

class SignedTimesheetUpload(BaseModel):
    """Model für hochgeladene unterschriebene Stundenzettel"""
    timesheet_id: str
    filename: str
    local_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    file_size: int

class WeeklyTimesheetCreate(BaseModel):
    week_start: str
    week_vehicle_id: Optional[str] = None
    entries: List[TimeEntry]

class TravelExpense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    date: str  # YYYY-MM-DD format
    description: str  # Beschreibung (z.B. "Fahrt nach Berlin")
    kilometers: float = 0.0  # Gefahrene Kilometer
    expenses: float = 0.0  # Reisekosten in Euro (Spesen, Bahntickets, etc.)
    customer_project: str = ""  # Optional: Kunde/Projekt
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "draft"  # draft, sent, approved

class TravelExpenseCreate(BaseModel):
    date: str
    description: str
    kilometers: float = 0.0
    expenses: float = 0.0
    customer_project: str = ""

class TravelExpenseUpdate(BaseModel):
    date: Optional[str] = None
    description: Optional[str] = None
    kilometers: Optional[float] = None
    expenses: Optional[float] = None
    customer_project: Optional[str] = None

class TravelExpenseReceipt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    local_path: str  # Pfad auf lokalem Bürorechner
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    file_size: int  # in Bytes
    exchange_proof_path: Optional[str] = None  # Pfad zum Nachweis des Euro-Betrags (z.B. Kontoauszug) bei Fremdwährung
    exchange_proof_filename: Optional[str] = None  # Dateiname des Nachweises

class TravelExpenseReportEntry(BaseModel):
    date: str  # YYYY-MM-DD
    location: str  # Ort aus Stundenzettel
    customer_project: str  # Kunde/Projekt
    travel_time_minutes: int  # Fahrzeit
    days_count: int = 1  # Anzahl Tage
    working_hours: float = 0.0  # Gutgeschriebene Arbeitsstunden aus Stundenzettel (für Abgleich mit Reisekosten)

class TravelExpenseReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    month: str  # YYYY-MM format
    entries: List[TravelExpenseReportEntry]  # Auto-gefüllt aus Stundenzetteln
    receipts: List[TravelExpenseReceipt] = []  # Hochgeladene PDFs
    status: str = "draft"  # draft, submitted, in_review, approved
    review_notes: Optional[str] = None  # Notizen von Agenten/Prüfung
    accounting_data: Optional[Dict[str, Any]] = None  # Ergebnis von Accounting Agent
    document_analyses: Optional[List[Dict[str, Any]]] = None  # Ergebnisse von Document Agent
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

class TravelExpenseReportUpdate(BaseModel):
    entries: Optional[List[TravelExpenseReportEntry]] = None

class Vehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    license_plate: str
    is_pool: bool = False
    assigned_user_id: Optional[str] = None
    assigned_user_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VehicleCreate(BaseModel):
    name: str
    license_plate: str
    is_pool: bool = False
    assigned_user_id: Optional[str] = None

class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    license_plate: Optional[str] = None
    is_pool: Optional[bool] = None
    assigned_user_id: Optional[str] = None

class VacationRequest(BaseModel):
    """Urlaubsantrag"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    working_days: int  # Anzahl Werktage (Mo-Fr)
    year: int  # Jahr des Urlaubs
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None  # user_id des Genehmigers
    notes: Optional[str] = None  # Optional: Notizen

class VacationRequestCreate(BaseModel):
    start_date: str
    end_date: str
    notes: Optional[str] = None

class VacationBalance(BaseModel):
    """Urlaubsguthaben pro Mitarbeiter pro Jahr"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    year: int
    total_days: int  # Gesamt verfügbare Urlaubstage (Mo-Fr)
    used_days: int = 0  # Verbrauchte Tage
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VacationBalanceUpdate(BaseModel):
    total_days: int

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_id: str
    sender: str  # "user" or "agent"
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SMTPConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    admin_email: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SMTPConfigCreate(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    admin_email: str

class Announcement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str  # HTML content
    image_url: Optional[str] = None  # Base64 encoded image or URL
    image_filename: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # user_id

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    image_filename: Optional[str] = None
    active: bool = True

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    image_filename: Optional[str] = None
    active: Optional[bool] = None

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_calendar_week(date_str: str) -> str:
    """Get calendar week from date string (YYYY-MM-DD)"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    year, week, _ = date_obj.isocalendar()
    return f"KW{week:02d}"

def sanitize_filename(name: str) -> str:
    """Sanitize name for filename usage"""
    # Replace spaces with underscores and remove special characters
    sanitized = re.sub(r'[^\w\-_.]', '_', name)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized

def _date_in_year_month(date_str: str, year: int, month: int) -> bool:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.year == year and d.month == month
    except Exception:
        return False

def get_german_holidays(year: int) -> set:
    """Holt deutsche (bundesweit) und sächsische Feiertage für ein Jahr"""
    try:
        import holidays
        # Deutsche Feiertage (bundesweit)
        de_holidays = holidays.Germany(years=year, prov=None)
        # Sächsische Feiertage (Bundesland: SN = Sachsen)
        sn_holidays = holidays.Germany(years=year, prov='SN')
        # Kombiniere beide Sets
        all_holidays = set(de_holidays.keys()) | set(sn_holidays.keys())
        return all_holidays
    except Exception as e:
        logger.warning(f"Fehler beim Laden der Feiertage: {e}")
        # Fallback: Manuelle Liste der wichtigsten Feiertage
        fallback_holidays = set()
        # Neujahr, Karfreitag, Ostermontag, Tag der Arbeit, Christi Himmelfahrt, Pfingstmontag, Tag der Deutschen Einheit, 1. Weihnachtstag, 2. Weihnachtstag
        # Diese sind immer in Deutschland
        # Für Sachsen: zusätzlich Reformationsfest (31.10) als Feiertag
        # Vereinfacht: Wir verwenden nur die Feiertage, die in der holidays-Bibliothek sind
        return fallback_holidays

def is_holiday(date_str: str) -> bool:
    """Prüft, ob ein Datum ein Feiertag ist (deutschlandweit oder Sachsen)"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year = date_obj.year
        holidays_set = get_german_holidays(year)
        return date_obj.date() in holidays_set
    except Exception:
        return False

def count_working_days(start_date: str, end_date: str) -> int:
    """Zählt Werktage (Mo-Fr) zwischen zwei Daten, Feiertage werden ausgeschlossen"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        if start > end:
            return 0
        
        # Hole Feiertage für alle Jahre, die der Zeitraum abdeckt
        years = set(range(start.year, end.year + 1))
        all_holidays = set()
        for year in years:
            all_holidays.update(get_german_holidays(year))
        
        count = 0
        current = start
        while current <= end:
            # 0 = Montag, 4 = Freitag
            if current.weekday() < 5:
                # Prüfe, ob es kein Feiertag ist
                if current.date() not in all_holidays:
                    count += 1
            current += timedelta(days=1)
        return count
    except Exception as e:
        logger.error(f"Fehler beim Zählen der Werktage: {e}")
        return 0

def get_vacation_dates_in_range(start_date: str, end_date: str, approved_requests: List[Dict]) -> List[str]:
    """Gibt alle Datumsstrings (YYYY-MM-DD) zurück, die in genehmigten Urlaubsanträgen liegen"""
    vacation_dates = []
    try:
        range_start = datetime.strptime(start_date, "%Y-%m-%d")
        range_end = datetime.strptime(end_date, "%Y-%m-%d")
        for req in approved_requests:
            if req.get("status") != "approved":
                continue
            req_start = datetime.strptime(req.get("start_date"), "%Y-%m-%d")
            req_end = datetime.strptime(req.get("end_date"), "%Y-%m-%d")
            current = max(req_start, range_start)
            end = min(req_end, range_end)
            while current <= end:
                if current.weekday() < 5:  # Mo-Fr
                    vacation_dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)
    except Exception:
        pass
    return list(set(vacation_dates))  # Remove duplicates

async def ensure_vehicle_access(vehicle_id: str, owner_user_id: str, db) -> Dict[str, Any]:
    """Validiert, dass ein Fahrzeug existiert und vom Nutzer genutzt werden darf."""
    vehicle = await db.vehicles.find_one({"id": vehicle_id})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Fahrzeug wurde nicht gefunden.")
    if not vehicle.get("is_pool") and vehicle.get("assigned_user_id") != owner_user_id:
        raise HTTPException(
            status_code=400,
            detail="Das ausgewählte Fahrzeug ist diesem Mitarbeiter nicht zugeordnet."
        )
    return vehicle

async def add_vacation_entries_to_timesheet(entries: List[TimeEntry], week_start: str, week_end: str, user_id: str, db) -> List[TimeEntry]:
    """Fügt automatisch genehmigte Urlaubstage als Einträge hinzu, falls noch nicht vorhanden.
    Feiertage werden als 'feiertag' eingetragen, nicht als 'urlaub'."""
    # Hole alle genehmigten Urlaubsanträge, die diese Woche überlappen
    approved_requests = await db.vacation_requests.find({
        "user_id": user_id,
        "status": "approved",
        "$or": [
            {"start_date": {"$lte": week_end, "$gte": week_start}},
            {"end_date": {"$lte": week_end, "$gte": week_start}},
            {"$and": [{"start_date": {"$lte": week_start}}, {"end_date": {"$gte": week_end}}]}
        ]
    }).to_list(100)
    
    # Erstelle Set von vorhandenen Einträgen-Daten
    existing_dates = {entry.date for entry in entries}
    
    # Hole Feiertage für die Woche
    week_start_dt = datetime.strptime(week_start, "%Y-%m-%d")
    week_end_dt = datetime.strptime(week_end, "%Y-%m-%d")
    years = set(range(week_start_dt.year, week_end_dt.year + 1))
    all_holidays = set()
    for year in years:
        all_holidays.update(get_german_holidays(year))
    
    new_entries = []
    current = week_start_dt
    while current <= week_end_dt:
        date_str = current.strftime("%Y-%m-%d")
        current_date = current.date()
        
        # Nur Werktage (Mo-Fr) und nicht bereits vorhanden
        if current.weekday() < 5 and date_str not in existing_dates:
            # Prüfe zuerst, ob es ein Feiertag ist
            if current_date in all_holidays:
                # Feiertag eintragen
                holiday_entry = TimeEntry(
                    date=date_str,
                    start_time="",
                    end_time="",
                    break_minutes=0,
                    tasks="",
                    customer_project="",
                    location="",
                    absence_type="feiertag",
                    travel_time_minutes=0,
                    include_travel_time=False
                )
                new_entries.append(holiday_entry)
            else:
                # Prüfe, ob dieser Tag in einem genehmigten Urlaub liegt
                for req in approved_requests:
                    req_start = datetime.strptime(req.get("start_date"), "%Y-%m-%d")
                    req_end = datetime.strptime(req.get("end_date"), "%Y-%m-%d")
                    if req_start <= current <= req_end:
                        # Erstelle Urlaubseintrag
                        vacation_entry = TimeEntry(
                            date=date_str,
                            start_time="",
                            end_time="",
                            break_minutes=0,
                            tasks="",
                            customer_project="",
                            location="",
                            absence_type="urlaub",
                            travel_time_minutes=0,
                            include_travel_time=False
                        )
                        new_entries.append(vacation_entry)
                        break  # Nur einmal pro Tag hinzufügen
        current += timedelta(days=1)
    
    # Kombiniere bestehende und neue Einträge, sortiert nach Datum
    all_entries = entries + new_entries
    all_entries.sort(key=lambda e: e.date)
    return all_entries

async def check_vacation_requirements(year: int, user_id: str, db) -> Dict[str, Any]:
    """Prüft, ob gesetzliche und betriebliche Anforderungen erfüllt sind:
    - Gesetzlich (BUrlG §7): Mindestens 2 Wochen am Stück (10 Werktage, Mo-Fr ohne Feiertage) - gesetzlicher Erholungsurlaub
    - Betrieblich: Mindestens 20 Tage insgesamt geplant - betriebliche Vorgabe
    - Betrieblich: Eingetragen bis 01.02. des Jahres - betriebliche Vorgabe
    """
    from datetime import date
    today = date.today()
    deadline = date(year, 2, 1)
    
    # Hole alle genehmigten Urlaubsanträge für das Jahr
    approved_requests = await db.vacation_requests.find({
        "user_id": user_id,
        "year": year,
        "status": "approved"
    }).to_list(100)
    
    total_days = sum(req.get("working_days", 0) for req in approved_requests)
    max_consecutive = 0
    current_consecutive = 0
    
    if approved_requests:
        # Sortiere nach Startdatum
        sorted_requests = sorted(approved_requests, key=lambda x: x.get("start_date", ""))
        for req in sorted_requests:
            days = req.get("working_days", 0)
            # 2 Wochen = 10 Werktage (Mo-Fr ohne Feiertage)
            if days >= 10:
                max_consecutive = max(max_consecutive, days)
            current_consecutive = max(current_consecutive, days)
    
    # 2 Wochen am Stück = 10 Werktage (gesetzlicher Jahresurlaub)
    meets_min_consecutive = max_consecutive >= 10
    meets_min_total = total_days >= 20
    meets_deadline = today <= deadline
    
    return {
        "meets_min_consecutive": meets_min_consecutive,
        "meets_min_total": meets_min_total,
        "meets_deadline": meets_deadline,
        "total_days": total_days,
        "max_consecutive": max_consecutive,
        "deadline_passed": today > deadline,
        "needs_reminder": not (meets_min_consecutive and meets_min_total and meets_deadline)
    }

def _entry_hours(entry: TimeEntry) -> float:
    """
    Calculate working hours including travel time if include_travel_time is True
    
    WICHTIG: Nur die Anreise zum Arbeitsort wird als Arbeitszeit gewertet.
    Die tägliche Fahrt Hotel-Kunde ist KEINE Arbeitszeit und sollte nicht als Fahrzeit erfasst werden.
    """
    hours = 0.0
    
    # Calculate regular working hours from start/end time
    if entry.start_time and entry.end_time:
        try:
            sh, sm = map(int, entry.start_time.split(":"))
            eh, em = map(int, entry.end_time.split(":"))
            start = sh * 60 + sm
            end = eh * 60 + em
            worked = max(0, end - start - int(entry.break_minutes))
            hours = max(0.0, worked / 60.0)
        except Exception:
            pass
    
    # Add travel time if checkbox is checked (only for travel to work location, not daily hotel-customer trips)
    # Note: This is always counted in DB for statistics, but only shown on PDF if include_travel_time is True
    # WICHTIG: Nur Anreise zum Arbeitsort zählt, nicht tägliche Fahrten Hotel-Kunde
    if entry.travel_time_minutes and entry.travel_time_minutes > 0:
        hours += entry.travel_time_minutes / 60.0
    
    return hours

async def generate_pdf_filename(timesheet: WeeklyTimesheet, user_name: str) -> str:
    """Generate PDF filename: [Mitarbeiter_Name]_[Kalenderwoche]_[fortlaufende Nummer]"""
    # Sanitize user name
    clean_name = sanitize_filename(user_name)
    
    # Get calendar week
    calendar_week = get_calendar_week(timesheet.week_start)
    
    # Find sequential number for this user and calendar week
    week_start_date = datetime.strptime(timesheet.week_start, "%Y-%m-%d")
    year = week_start_date.year
    
    # Count existing timesheets for this user in the same calendar week
    existing_timesheets = await db.timesheets.find({
        "user_id": timesheet.user_id,
        "created_at": {
            "$gte": datetime(year, 1, 1),
            "$lt": datetime(year + 1, 1, 1)
        }
    }).to_list(1000)
    
    # Filter by same calendar week
    same_week_count = 0
    for existing in existing_timesheets:
        existing_week = get_calendar_week(existing["week_start"])
        if existing_week == calendar_week:
            same_week_count += 1
    
    # Sequential number (current timesheet is included in count)
    sequential_number = f"{same_week_count:03d}"
    
    filename = f"{clean_name}_{calendar_week}_{sequential_number}.pdf"
    return filename

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        # Remove MongoDB internal id
        user.pop("_id", None)
        # Handle backward compatibility: convert is_admin to role if role doesn't exist
        if "role" not in user and "is_admin" in user:
            user["role"] = "admin" if user["is_admin"] else "user"
        # Set default weekly_hours if not present
        if "weekly_hours" not in user:
            user["weekly_hours"] = 40.0
        return User(**user)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def get_accounting_or_admin_user(current_user: User = Depends(get_current_user)):
    """Allow admin or accounting role to access"""
    if current_user.role not in ["admin", "accounting"]:
        raise HTTPException(status_code=403, detail="Admin or Accounting access required")
    return current_user

def generate_timesheet_pdf(timesheet: WeeklyTimesheet) -> bytes:
    """Generate single-page PDF for weekly timesheet in landscape format matching company template"""
    buffer = io.BytesIO()
    # Use landscape orientation (A4 rotated)  
    from reportlab.lib.pagesizes import A4, landscape
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    
    # Company colors
    company_red = colors.Color(233/255, 1/255, 24/255)  # #e90118
    light_gray = colors.Color(179/255, 179/255, 181/255)  # #b3b3b5
    dark_gray = colors.Color(90/255, 90/255, 90/255)     # #5a5a5a
    
    story = []
    
    # Page width for layout calculations
    page_width = landscape(A4)[0] - 40  # minus margins
    
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=dark_gray,
        alignment=1,  # Center
        spaceAfter=20
    )
    
    # Add title
    story.append(Paragraph("<b>STUNDENZETTEL</b>", title_style))
    
    # Add company header info in top right
    company_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=8,
        textColor=dark_gray,
        alignment=2,  # Right align
    )
    
    company_info = f"""<b>Byte Commander</b><br/>
    Tick Guard - Zeiterfassung & Reisekosten"""
    
    story.append(Paragraph(company_info, company_style))
    story.append(Spacer(1, 10))
    
    # Project and Customer info row
    project_style = ParagraphStyle(
        'ProjectInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=dark_gray,
    )
    
    # Extract project info from first entry if available
    project_info = ""
    customer_info = ""
    if timesheet.entries:
        project_info = timesheet.entries[0].customer_project
        customer_info = timesheet.entries[0].customer_project
    
    project_customer_table = Table([
        [f"Projekt: {project_info}", f"Kunde: {customer_info}"]
    ], colWidths=[page_width*0.5, page_width*0.5])
    
    project_customer_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), dark_gray),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(project_customer_table)
    story.append(Spacer(1, 10))
    
    # Main timesheet table according to template
    table_headers = ["Datum", "Startzeit", "Endzeit", "Pause", "Beschreibung", "Arbeitszeit"]
    table_data = [table_headers]
    
    # Days of the week in German
    day_names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    
    # Calculate total hours
    total_hours = 0
    
    # Get week dates
    from datetime import datetime, timedelta
    week_start_date = datetime.strptime(timesheet.week_start, "%Y-%m-%d")
    
    # Build table rows for each day
    entries_by_date = {entry.date: entry for entry in timesheet.entries}
    
    for i in range(7):  # Monday to Sunday
        current_date = week_start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        display_date = day_names[i]  # Use German day names
        
        row = [display_date, "", "", "", "", ""]  # Default empty row
        
        if date_str in entries_by_date:
            entry = entries_by_date[date_str]
            
            # Check for absence type (Urlaub, Krankheit, Feiertag)
            absence_labels = {
                "urlaub": "Urlaub",
                "krankheit": "Krankheit",
                "feiertag": "Feiertag"
            }
            
            if entry.absence_type and entry.absence_type in absence_labels:
                # Show absence type in description
                row[4] = absence_labels[entry.absence_type]
                if entry.tasks:
                    row[4] += f" - {entry.tasks}"
                # No times shown for absence days
                row[5] = "0.0h"
            elif entry.start_time and entry.end_time:
                # Regular working day with times
                row[1] = entry.start_time  # Startzeit
                row[2] = entry.end_time    # Endzeit
                row[3] = f"{entry.break_minutes} Min"  # Pause
                
                # Calculate daily hours from start/end time
                start_parts = entry.start_time.split(':')
                end_parts = entry.end_time.split(':')
                start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
                end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
                worked_minutes = end_minutes - start_minutes - entry.break_minutes
                daily_hours = worked_minutes / 60
                
                # Add travel time to displayed hours only if include_travel_time is True
                # WICHTIG: Nur Anreise zum Arbeitsort zählt, nicht tägliche Fahrten Hotel-Kunde
                if entry.include_travel_time and entry.travel_time_minutes and entry.travel_time_minutes > 0:
                    daily_hours += entry.travel_time_minutes / 60.0
                    # Add travel time info to description
                    travel_hours = entry.travel_time_minutes / 60.0
                    if entry.tasks:
                        row[4] = f"{entry.tasks} (Fahrzeit Anreise: {travel_hours:.1f}h)"
                    else:
                        row[4] = f"Fahrzeit Anreise: {travel_hours:.1f}h"
                else:
                    # Regular description without travel time
                    row[4] = entry.tasks if entry.tasks else ""
                
                # Note: Travel time is ALWAYS counted in DB (_entry_hours), but only shown on PDF if include_travel_time=True
                # WICHTIG: Nur Anreise zum Arbeitsort zählt als Arbeitszeit, nicht tägliche Fahrten Hotel-Kunde
                total_hours += daily_hours
                row[5] = f"{daily_hours:.1f}h"  # Arbeitszeit
            else:
                # Entry exists but no times - just show description
                row[4] = entry.tasks if entry.tasks else ""
                row[5] = "0.0h"
        
        table_data.append(row)
    
    # Add total hours row
    table_data.append(["", "", "", "", "Gesamtstunden:", f"{total_hours:.1f}h"])
    
    # Create the main table
    col_widths = [page_width*0.15, page_width*0.15, page_width*0.15, page_width*0.1, page_width*0.3, page_width*0.15]
    main_table = Table(table_data, colWidths=col_widths)
    
    # Style the table according to template
    main_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('ALIGN', (0, 1), (-1, -2), 'CENTER'),
        ('ALIGN', (4, 1), (4, -2), 'LEFT'),  # Description column left-aligned
        
        # Total row
        ('BACKGROUND', (0, -1), (-1, -1), light_gray),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 10),
        ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
        
        # All cells
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(main_table)
    story.append(Spacer(1, 20))
    
    # Signature section
    signature_table = Table([
        [f"Datum: {timesheet.created_at.strftime('%d.%m.%Y')}", "Unterschrift Kunde: ___________________________"],
        [f"Mitarbeiter: {timesheet.user_name}", "Unterschrift Mitarbeiter: ______________________"]
    ], colWidths=[page_width*0.5, page_width*0.5])
    
    signature_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), dark_gray),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(signature_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_accounting_report_pdf(stats_response: AccountingStatsResponse) -> bytes:
    """Generate PDF report for accounting with detailed monthly statistics"""
    buffer = io.BytesIO()
    from reportlab.lib.pagesizes import A4, landscape
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    
    # Company colors
    company_red = colors.Color(233/255, 1/255, 24/255)  # #e90118
    light_gray = colors.Color(179/255, 179/255, 181/255)  # #b3b3b5
    dark_gray = colors.Color(90/255, 90/255, 90/255)     # #5a5a5a
    
    story = []
    
    # Page width for layout calculations
    page_width = landscape(A4)[0] - 40  # minus margins
    
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=dark_gray,
        alignment=1,  # Center
        spaceAfter=20
    )
    
    # Add title
    month_date = datetime.strptime(f"{stats_response.month}-01", "%Y-%m-%d")
    month_name = month_date.strftime("%B %Y")
    story.append(Paragraph(f"<b>BUCHHALTUNGSBERICHT - {month_name}</b>", title_style))
    
    # Add company header info
    company_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=8,
        textColor=dark_gray,
        alignment=2,  # Right align
    )
    
    company_info = f"""<b>Byte Commander</b><br/>
    Tick Guard - Zeiterfassung & Reisekosten"""
    
    story.append(Paragraph(company_info, company_style))
    story.append(Spacer(1, 20))
    
    # Main statistics table
    table_headers = [
        "Mitarbeiter", 
        "Monatsgesamt-\nstunden*", 
        "Stunden auf\nStundenzetteln", 
        "Fahrzeit\ngesamt", 
        "Fahrzeit auf\nStundenzetteln",
        "Kilometer",
        "Reisekosten\n(€)",
        "Anzahl\nStundenzettel"
    ]
    table_data = [table_headers]
    
    # Calculate totals
    total_hours = 0.0
    total_hours_on_timesheets = 0.0
    total_travel_hours = 0.0
    total_travel_hours_on_timesheets = 0.0
    total_travel_kilometers = 0.0
    total_travel_expenses = 0.0
    total_timesheets = 0
    
    for stat in stats_response.stats:
        table_data.append([
            stat.user_name,
            f"{stat.total_hours:.2f}h",
            f"{stat.hours_on_timesheets:.2f}h",
            f"{stat.travel_hours:.2f}h",
            f"{stat.travel_hours_on_timesheets:.2f}h",
            f"{stat.travel_kilometers:.1f} km" if stat.travel_kilometers > 0 else "-",
            f"{stat.travel_expenses:.2f} €" if stat.travel_expenses > 0 else "-",
            str(stat.timesheets_count)
        ])
        total_hours += stat.total_hours
        total_hours_on_timesheets += stat.hours_on_timesheets
        total_travel_hours += stat.travel_hours
        total_travel_hours_on_timesheets += stat.travel_hours_on_timesheets
        total_travel_kilometers += stat.travel_kilometers
        total_travel_expenses += stat.travel_expenses
        total_timesheets += stat.timesheets_count
    
    # Add total row
    table_data.append([
        "<b>Gesamt</b>",
        f"<b>{total_hours:.2f}h</b>",
        f"<b>{total_hours_on_timesheets:.2f}h</b>",
        f"<b>{total_travel_hours:.2f}h</b>",
        f"<b>{total_travel_hours_on_timesheets:.2f}h</b>",
        f"<b>{total_travel_kilometers:.1f} km</b>",
        f"<b>{total_travel_expenses:.2f} €</b>",
        f"<b>{total_timesheets}</b>"
    ])
    
    # Create the main table
    col_widths = [
        page_width*0.18,
        page_width*0.12,
        page_width*0.12,
        page_width*0.12,
        page_width*0.12,
        page_width*0.10,
        page_width*0.12,
        page_width*0.12
    ]
    main_table = Table(table_data, colWidths=col_widths)
    
    # Style the table
    main_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (-2, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-2, -2), 9),
        ('ALIGN', (0, 1), (-1, -2), 'CENTER'),
        ('ALIGN', (0, 1), (0, -2), 'LEFT'),  # Name left-aligned
        
        # Total row
        ('BACKGROUND', (0, -1), (-1, -1), light_gray),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 10),
        ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, -1), (0, -1), 'LEFT'),
        
        # All cells
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(main_table)
    story.append(Spacer(1, 20))
    
    # Add explanation
    explanation_style = ParagraphStyle(
        'Explanation',
        parent=styles['Normal'],
        fontSize=8,
        textColor=dark_gray,
        alignment=0,  # Left align
    )
    
    explanation = """
    <b>Erklärung:</b><br/>
    • <b>Monatsgesamtstunden:</b> Alle Stunden inkl. Fahrzeit (wie in Datenbank gespeichert)<br/>
    • <b>Stunden auf Stundenzetteln:</b> Stunden die tatsächlich auf den Stundenzettel-PDFs erscheinen<br/>
    • <b>Fahrzeit gesamt:</b> Gesamte erfasste Fahrzeit (unabhängig von "Weiterberechnen")<br/>
    • <b>Fahrzeit auf Stundenzetteln:</b> Fahrzeit die auf den Stundenzettel-PDFs erscheint (nur wenn "Weiterberechnen" angehakt)<br/>
    • <b>Kilometer:</b> Gesamtkilometer für Reisekosten<br/>
    • <b>Reisekosten:</b> Gesamte Reisekosten in Euro (Spesen, Bahntickets, etc.)
    """
    
    story.append(Paragraph(explanation, explanation_style))
    story.append(Spacer(1, 20))
    
    # Add date
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=9,
        textColor=dark_gray,
        alignment=2,  # Right align
    )
    
    story.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M Uhr')}", date_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Routes
@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "is_admin": current_user.is_admin,  # Backward compatibility
        "role": current_user.role
    }

@limiter.limit("5/minute")  # Max 5 Login-Versuche pro Minute
@api_router.post("/auth/login")
async def login(request: Request, user_login: UserLogin):
    requested_email = user_login.email.strip()
    user = await db.users.find_one({"email": requested_email})
    if not user:
        normalized_email = requested_email.lower()
        if normalized_email != requested_email:
            user = await db.users.find_one({"email": normalized_email})
        else:
            normalized_email = requested_email.lower()
    else:
        normalized_email = requested_email.lower()

    if not user:
        admin_candidates = LEGACY_ADMIN_EMAILS | {DEFAULT_ADMIN_EMAIL}
        if normalized_email in admin_candidates:
            created = await create_admin_user(email=normalized_email)
            if created:
                logger.info("Admin user auto-created during login attempt.")
            user = await db.users.find_one({"email": normalized_email})
    if not user or not verify_password(user_login.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # 2FA is mandatory - check if user has 2FA setup
    if not user.get("two_fa_secret") or not user.get("two_fa_enabled"):
        # User needs to setup 2FA first (no secret OR secret exists but not enabled yet)
        # Generate a temporary token for 2FA setup (valid for 10 minutes)
        setup_token = create_access_token(
            data={"sub": user["email"], "scope": "2fa_setup"}, expires_delta=timedelta(minutes=10)
        )
        return {"requires_2fa_setup": True, "setup_token": setup_token}
    
    # 2FA is mandatory - user must provide OTP (only if 2FA is fully enabled)
    if not user_login.otp:
        # User needs to provide 2FA code
        temp_token = create_access_token(
            data={"sub": user["email"], "scope": "2fa"}, expires_delta=timedelta(minutes=5)
        )
        return {"requires_2fa": True, "temp_token": temp_token}
    
    # Verify provided OTP
    if not user.get("two_fa_enabled"):
        # Secret exists but 2FA not enabled yet - still require verification
        totp = pyotp.TOTP(user["two_fa_secret"])
        if not totp.verify(user_login.otp, valid_window=1):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")
        # Auto-enable 2FA if secret exists and code is valid
        await db.users.update_one({"id": user["id"]}, {"$set": {"two_fa_enabled": True}})
    else:
        # Normal 2FA verification
        totp = pyotp.TOTP(user["two_fa_secret"])
        if not totp.verify(user_login.otp, valid_window=1):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    # Handle backward compatibility: convert is_admin to role if role doesn't exist
    user_role = user.get("role")
    if not user_role and "is_admin" in user:
        user_role = "admin" if user["is_admin"] else "user"
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user.get("is_admin", False),  # Backward compatibility
            "role": user_role or "user"
        }
    }

@limiter.limit("3/hour")  # Max 3 Registrierungen pro Stunde
@api_router.post("/auth/register")
async def register(request: Request, user_create: UserCreate, current_user: User = Depends(get_admin_user)):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_create.password)
    # Generate 2FA secret automatically for new users (2FA is mandatory)
    two_fa_secret = pyotp.random_base32()
    
    user = User(
        email=user_create.email,
        name=user_create.name,
        role=user_create.role,
        hashed_password=hashed_password,
        weekly_hours=getattr(user_create, 'weekly_hours', 40.0),
        two_fa_secret=two_fa_secret,
        two_fa_enabled=False  # Will be enabled after first 2FA setup/verification
    )
    
    user_dict = user.model_dump()
    # Also store is_admin for backward compatibility
    user_dict["is_admin"] = user.role == "admin"
    await db.users.insert_one(user_dict)
    return {"message": "User created successfully", "user_id": user.id}

@api_router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(current_user: User = Depends(get_admin_user)):
    users = await db.users.find().to_list(1000)
    result = []
    for user in users:
        # Handle backward compatibility
        role = user.get("role")
        if not role and "is_admin" in user:
            role = "admin" if user["is_admin"] else "user"
        result.append({
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user.get("is_admin", False),  # Backward compatibility
            "role": role or "user"
        })
    return result

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate, current_user: User = Depends(get_admin_user)):
    # Find user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_data = {}
    if user_update.email:
        # Check if email already exists (except for current user)
        existing_user = await db.users.find_one({"email": user_update.email, "id": {"$ne": user_id}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        update_data["email"] = user_update.email
    
    if user_update.name:
        update_data["name"] = user_update.name
    
    if user_update.role is not None:
        update_data["role"] = user_update.role
        # Also update is_admin for backward compatibility
        update_data["is_admin"] = user_update.role == "admin"
    elif user_update.is_admin is not None:
        # Backward compatibility: convert is_admin to role
        update_data["role"] = "admin" if user_update.is_admin else "user"
        update_data["is_admin"] = user_update.is_admin
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    return {"message": "User updated successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_admin_user)):
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Find user to delete
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if this is an admin user
    user_role = user.get("role", "admin" if user.get("is_admin") else "user")
    if user_role == "admin":
        # Count total number of admin users
        admin_count = await db.users.count_documents({"$or": [{"role": "admin"}, {"is_admin": True}]})
        if admin_count <= 1:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete the last admin user. At least one admin must remain in the system."
            )
    
    # Delete user and their timesheets
    await db.users.delete_one({"id": user_id})
    await db.timesheets.delete_many({"user_id": user_id})
    
    return {"message": "User and associated timesheets deleted successfully"}

@api_router.get("/vehicles", response_model=List[Vehicle])
async def get_vehicles(current_user: User = Depends(get_admin_user)):
    vehicles = await db.vehicles.find().sort("name", 1).to_list(1000)
    sanitized: List[Vehicle] = []
    for vehicle in vehicles:
        vehicle.pop("_id", None)
        sanitized.append(Vehicle(**vehicle))
    return sanitized

@api_router.post("/vehicles", response_model=Vehicle)
async def create_vehicle(vehicle_create: VehicleCreate, current_user: User = Depends(get_admin_user)):
    name = vehicle_create.name.strip()
    license_plate = vehicle_create.license_plate.strip()
    if not name or not license_plate:
        raise HTTPException(status_code=400, detail="Name and licence plate are required")
    
    assigned_user_id: Optional[str] = None
    assigned_user_name: Optional[str] = None
    
    if vehicle_create.is_pool:
        # Pool vehicles must not have an assigned user
        if vehicle_create.assigned_user_id:
            raise HTTPException(
                status_code=400,
                detail="Poolfahrzeuge dürfen keinem bestimmten Mitarbeiter zugewiesen sein."
            )
    else:
        if not vehicle_create.assigned_user_id:
            raise HTTPException(
                status_code=400,
                detail="Für ein persönliches Fahrzeug muss ein Mitarbeiter ausgewählt werden."
            )
        user = await db.users.find_one({"id": vehicle_create.assigned_user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
        assigned_user_id = user["id"]
        assigned_user_name = user["name"]
    
    vehicle = Vehicle(
        name=name,
        license_plate=license_plate,
        is_pool=vehicle_create.is_pool,
        assigned_user_id=assigned_user_id,
        assigned_user_name=assigned_user_name
    )
    await db.vehicles.insert_one(vehicle.model_dump())
    return vehicle

@api_router.put("/vehicles/{vehicle_id}", response_model=Vehicle)
async def update_vehicle(vehicle_id: str, vehicle_update: VehicleUpdate, current_user: User = Depends(get_admin_user)):
    existing = await db.vehicles.find_one({"id": vehicle_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Fahrzeug nicht gefunden")
    
    name = vehicle_update.name.strip() if vehicle_update.name is not None else existing.get("name", "")
    license_plate = (
        vehicle_update.license_plate.strip()
        if vehicle_update.license_plate is not None
        else existing.get("license_plate", "")
    )
    if not name or not license_plate:
        raise HTTPException(status_code=400, detail="Name und Kennzeichen dürfen nicht leer sein.")
    
    is_pool = vehicle_update.is_pool if vehicle_update.is_pool is not None else existing.get("is_pool", False)
    assigned_user_id: Optional[str]
    assigned_user_name: Optional[str]
    
    if is_pool:
        assigned_user_id = None
        assigned_user_name = None
    else:
        # Determine user to assign: update value if provided, otherwise keep existing
        user_id_candidate = vehicle_update.assigned_user_id
        if user_id_candidate is None:
            user_id_candidate = existing.get("assigned_user_id")
        if not user_id_candidate:
            raise HTTPException(
                status_code=400,
                detail="Für ein persönliches Fahrzeug muss ein Mitarbeiter ausgewählt werden."
            )
        user = await db.users.find_one({"id": user_id_candidate})
        if not user:
            raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
        assigned_user_id = user["id"]
        assigned_user_name = user["name"]
    
    update_data = {
        "name": name,
        "license_plate": license_plate,
        "is_pool": is_pool,
        "assigned_user_id": assigned_user_id,
        "assigned_user_name": assigned_user_name,
        "updated_at": datetime.utcnow()
    }
    
    await db.vehicles.update_one({"id": vehicle_id}, {"$set": update_data})
    updated_vehicle = await db.vehicles.find_one({"id": vehicle_id})
    updated_vehicle.pop("_id", None)
    return Vehicle(**updated_vehicle)

@api_router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: str, current_user: User = Depends(get_admin_user)):
    result = await db.vehicles.delete_one({"id": vehicle_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Fahrzeug nicht gefunden")
    return {"message": "Fahrzeug wurde gelöscht"}

@api_router.get("/vehicles/available", response_model=List[Vehicle])
async def get_available_vehicles(current_user: User = Depends(get_current_user)):
    """Gibt alle Poolfahrzeuge sowie persönliche Fahrzeuge des aktuellen Users zurück."""
    vehicles = await db.vehicles.find(
        {
            "$or": [
                {"is_pool": True},
                {"assigned_user_id": current_user.id},
            ]
        }
    ).sort("name", 1).to_list(100)
    sanitized: List[Vehicle] = []
    for vehicle in vehicles:
        vehicle.pop("_id", None)
        sanitized.append(Vehicle(**vehicle))
    return sanitized

@api_router.post("/auth/change-password")
async def change_password(password_change: PasswordChange, current_user: User = Depends(get_current_user)):
    # Verify current password
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    new_hashed_password = get_password_hash(password_change.new_password)
    await db.users.update_one(
        {"id": current_user.id}, 
        {"$set": {"hashed_password": new_hashed_password}}
    )
    
    return {"message": "Password changed successfully"}

# 2FA endpoints
@api_router.post("/auth/2fa/verify")
async def verify_two_fa(payload: TwoFAVerify):
    # Validate temp token
    try:
        data = jwt.decode(payload.temp_token, SECRET_KEY, algorithms=[ALGORITHM])
        if data.get("scope") != "2fa":
            raise HTTPException(status_code=400, detail="Invalid 2FA token")
        email = data.get("sub")
        user = await db.users.find_one({"email": email})
        if not user or not user.get("two_fa_enabled") or not user.get("two_fa_secret"):
            raise HTTPException(status_code=400, detail="2FA not enabled for user")
        totp = pyotp.TOTP(user["two_fa_secret"])
        if not totp.verify(payload.otp, valid_window=1):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

        # On success, issue normal access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "is_admin": user["is_admin"]
            }
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired 2FA token")

@api_router.post("/auth/2fa/setup", response_model=TwoFASetupResponse)
async def setup_two_fa(current_user: User = Depends(get_current_user)):
    """Setup 2FA - generates QR code for Google Authenticator"""
    # Check if user already has a secret
    user = await db.users.find_one({"id": current_user.id})
    if user and user.get("two_fa_secret"):
        secret = user["two_fa_secret"]
    else:
        # Generate new secret if none exists
        secret = pyotp.random_base32()
        await db.users.update_one({"id": current_user.id}, {"$set": {"two_fa_secret": secret}})
    
    issuer = COMPANY_INFO["name"]
    otpauth_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name=issuer)
    return {"secret": secret, "otpauth_uri": otpauth_uri}

@api_router.post("/auth/2fa/initial-setup")
async def initial_setup_2fa(payload: TwoFAVerify):
    """Initial 2FA setup endpoint - can be called with setup_token from login"""
    # Validate setup token
    try:
        data = jwt.decode(payload.temp_token, SECRET_KEY, algorithms=[ALGORITHM])
        if data.get("scope") != "2fa_setup":
            raise HTTPException(status_code=400, detail="Invalid setup token")
        email = data.get("sub")
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user already has 2FA enabled
        if user.get("two_fa_enabled") and user.get("two_fa_secret"):
            raise HTTPException(status_code=400, detail="2FA already enabled")
        
        # Generate secret if not exists
        if not user.get("two_fa_secret"):
            secret = pyotp.random_base32()
            await db.users.update_one({"id": user["id"]}, {"$set": {"two_fa_secret": secret}})
            user["two_fa_secret"] = secret
        
        # Verify the OTP code
        totp = pyotp.TOTP(user["two_fa_secret"])
        if not totp.verify(payload.otp, valid_window=1):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")
        
        # Enable 2FA and issue access token
        await db.users.update_one({"id": user["id"]}, {"$set": {"two_fa_enabled": True}})
        
        # Return QR code URI for user to scan
        issuer = COMPANY_INFO["name"]
        otpauth_uri = pyotp.totp.TOTP(user["two_fa_secret"]).provisioning_uri(name=user["email"], issuer_name=issuer)
        
        # Issue normal access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "otpauth_uri": otpauth_uri,
            "secret": user["two_fa_secret"],
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "is_admin": user.get("is_admin", False),
                "role": user.get("role", "user")
            }
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Setup token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired setup token: {str(e)}")

@api_router.get("/auth/2fa/setup-qr")
async def get_setup_qr(setup_token: str):
    """Get QR code for 2FA setup without authentication"""
    try:
        data = jwt.decode(setup_token, SECRET_KEY, algorithms=[ALGORITHM])
        if data.get("scope") != "2fa_setup":
            raise HTTPException(status_code=400, detail="Invalid setup token")
        email = data.get("sub")
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate secret if not exists
        if not user.get("two_fa_secret"):
            secret = pyotp.random_base32()
            await db.users.update_one({"id": user["id"]}, {"$set": {"two_fa_secret": secret}})
            user["two_fa_secret"] = secret
        
        issuer = COMPANY_INFO["name"]
        otpauth_uri = pyotp.totp.TOTP(user["two_fa_secret"]).provisioning_uri(name=user["email"], issuer_name=issuer)
        
        return {"secret": user["two_fa_secret"], "otpauth_uri": otpauth_uri}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Setup token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired setup token: {str(e)}")

@api_router.post("/auth/2fa/enable")
async def enable_two_fa(verification: TwoFAVerify, current_user: User = Depends(get_current_user)):
    # Use current user's stored secret and verify code, then enable
    user = await db.users.find_one({"id": current_user.id})
    if not user or not user.get("two_fa_secret"):
        raise HTTPException(status_code=400, detail="2FA setup required first")
    totp = pyotp.TOTP(user["two_fa_secret"])
    if not totp.verify(verification.otp, valid_window=1):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    await db.users.update_one({"id": current_user.id}, {"$set": {"two_fa_enabled": True}})
    return {"message": "2FA enabled"}

@api_router.post("/auth/2fa/disable")
async def disable_two_fa(current_user: User = Depends(get_admin_user)):
    """Disable 2FA - only allowed for admins (2FA is mandatory for all users)"""
    await db.users.update_one({"id": current_user.id}, {"$set": {"two_fa_enabled": False, "two_fa_secret": None}})
    return {"message": "2FA disabled (admin only)"}

# Stats: total sent hours per user per month (YYYY-MM)
@api_router.get("/stats/monthly", response_model=MonthlyStatsResponse)
async def get_monthly_stats(month: str, current_user: User = Depends(get_current_user)):
    # Validate month format
    try:
        year, mon = map(int, month.split("-"))
        _ = datetime(year, mon, 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    # Query only sent or approved timesheets for stats (but only approved count as working hours)
    query = {"status": {"$in": ["sent", "approved"]}}
    if not current_user.can_view_all_data():
        query["user_id"] = current_user.id

    ts = await db.timesheets.find(query).to_list(5000)
    
    # Get all users to access weekly_hours
    all_users = await db.users.find({}).to_list(1000)
    users_by_id = {u["id"]: u for u in all_users}

    # Aggregate hours per user für den Monat – NUR unterschriebene (hochgeladene) und freigegebene Stundenzettel zählen
    # (Anforderung: Stunden werden ausschließlich anhand vom Kunden unterzeichneter und hochgeladener PDFs erfasst)
    user_totals: Dict[str, Dict[str, Any]] = {}
    for t in ts:
        user_id = t.get("user_id")
        user_name = t.get("user_name", "")
        entries = t.get("entries", [])
        timesheet_status = t.get("status", "draft")
        # Nur zählen, wenn unterschriebener Stundenzettel vorhanden ist
        if not t.get("signed_pdf_path"):
            continue
        
        # Only count approved timesheets as working hours
        if timesheet_status != "approved":
            continue
            
        user = users_by_id.get(user_id, {})
        weekly_hours = user.get("weekly_hours", 40.0)
        hours_per_day = weekly_hours / 5.0  # Calculate hours per working day (assuming 5-day week)
        
        monthly_hours = 0.0
        for e in entries:
            try:
                # Works with dict entries or already validated
                e_date = e.get("date") if isinstance(e, dict) else e.date
                if _date_in_year_month(e_date, year, mon):
                    entry_obj = e if isinstance(e, dict) else e.model_dump()
                    te = TimeEntry(**entry_obj)
                    
                    # Check for absence (Urlaub, Krankheit, Feiertag) - add hours per day
                    if te.absence_type and te.absence_type in ["urlaub", "krankheit", "feiertag"]:
                        monthly_hours += hours_per_day
                    else:
                        # Regular working hours (always includes travel time for approved timesheets)
                        monthly_hours += _entry_hours(te)
            except Exception:
                continue
        if monthly_hours <= 0:
            continue
        if user_id not in user_totals:
            user_totals[user_id] = {"user_name": user_name, "total_hours": 0.0}
        user_totals[user_id]["total_hours"] += monthly_hours

    stats: List[MonthlyUserStat] = []
    for uid, data in user_totals.items():
        stats.append(MonthlyUserStat(user_id=uid, user_name=data["user_name"], month=month, total_hours=round(data["total_hours"], 2)))

    # For regular users, ensure at least their user appears with 0 if none found
    if not current_user.can_view_all_data() and not stats:
        stats.append(MonthlyUserStat(user_id=current_user.id, user_name=current_user.name, month=month, total_hours=0.0))

    # Sort by user_name
    stats.sort(key=lambda s: s.user_name.lower())
    return MonthlyStatsResponse(month=month, stats=stats)

# Rank of current user among all users for given month (based on sent timesheets)
@api_router.get("/stats/monthly/rank", response_model=MonthlyRankResponse)
async def get_monthly_rank(month: str, current_user: User = Depends(get_current_user)):
    # Validate month format
    try:
        year, mon = map(int, month.split("-"))
        _ = datetime(year, mon, 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    # All sent or approved timesheets
    ts = await db.timesheets.find({"status": {"$in": ["sent", "approved"]}}).to_list(5000)

    # Get all users to access weekly_hours
    all_users = await db.users.find({}).to_list(1000)
    users_by_id = {u["id"]: u for u in all_users}
    
    # Aggregate totals per user – nur unterschriebene (hochgeladene) und freigegebene Stundenzettel zählen
    totals: Dict[str, float] = {}
    names: Dict[str, str] = {}
    for t in ts:
        timesheet_status = t.get("status", "draft")
        # Nur zählen, wenn unterschriebener Stundenzettel vorhanden ist
        if not t.get("signed_pdf_path"):
            continue
        # Only count approved timesheets
        if timesheet_status != "approved":
            continue
            
        uid = t.get("user_id")
        names[uid] = t.get("user_name", names.get(uid, ""))
        entries = t.get("entries", [])
        user = users_by_id.get(uid, {})
        weekly_hours = user.get("weekly_hours", 40.0)
        hours_per_day = weekly_hours / 5.0
        
        hours = 0.0
        for e in entries:
            try:
                e_date = e.get("date") if isinstance(e, dict) else e.date
                if _date_in_year_month(e_date, year, mon):
                    entry_obj = e if isinstance(e, dict) else e.model_dump()
                    te = TimeEntry(**entry_obj)
                    
                    # Check for absence - add hours per day
                    if te.absence_type and te.absence_type in ["urlaub", "krankheit", "feiertag"]:
                        hours += hours_per_day
                    else:
                        hours += _entry_hours(te)
            except Exception:
                continue
        if hours > 0:
            totals[uid] = totals.get(uid, 0.0) + hours

    # Ensure current user present (with 0 if none)
    seen_users = set(totals.keys())
    seen_users.add(current_user.id)

    # Build sorted ranking list (descending by hours)
    ranking = sorted([(uid, totals.get(uid, 0.0)) for uid in seen_users], key=lambda x: x[1], reverse=True)

    # Determine 1-based rank of current user (handle ties: same hours -> same rank, standard competition ranking)
    rank = 1
    last_hours = None
    last_rank = 0
    for idx, (uid, hrs) in enumerate(ranking, start=1):
        if last_hours is None or hrs < last_hours:
            last_rank = idx
            last_hours = hrs
        if uid == current_user.id:
            rank = last_rank
            break

    return MonthlyRankResponse(month=month, rank=rank, total_users=len(seen_users))

# Accounting endpoints - detailed statistics for accounting department
@api_router.get("/accounting/monthly-stats", response_model=AccountingStatsResponse)
async def get_accounting_monthly_stats(month: str, current_user: User = Depends(get_accounting_or_admin_user)):
    """Get detailed monthly statistics for accounting - includes all hours and travel time breakdown"""
    # Validate month format
    try:
        year, mon = map(int, month.split("-"))
        _ = datetime(year, mon, 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    # Get all timesheets (all statuses for accounting view)
    ts = await db.timesheets.find({}).to_list(5000)
    
    # Get all travel expenses for the month
    travel_expenses = []
    async for expense in db.travel_expenses.find({}):
        exp_date = expense.get("date", "")
        if _date_in_year_month(exp_date, year, mon):
            travel_expenses.append(expense)
    
    # Get all users to access weekly_hours for absence calculation
    all_users = await db.users.find({}).to_list(1000)
    users_by_id = {u["id"]: u for u in all_users}

    # Aggregate detailed statistics per user
    user_stats: Dict[str, Dict[str, Any]] = {}
    timesheets_by_user: Dict[str, set] = {}  # Track unique timesheets per user
    
    for t in ts:
        user_id = t.get("user_id")
        user_name = t.get("user_name", "")
        entries = t.get("entries", [])
        timesheet_id = t.get("id")
        
        # Initialize user stats if needed
        if user_id not in user_stats:
            user_stats[user_id] = {
                "user_name": user_name,
                "total_hours": 0.0,
                "hours_on_timesheets": 0.0,
                "travel_hours": 0.0,
                "travel_hours_on_timesheets": 0.0,
                "travel_kilometers": 0.0,
                "travel_expenses": 0.0,
                "timesheets_count": 0
            }
            timesheets_by_user[user_id] = set()
        
        monthly_total_hours = 0.0  # Alle Stunden inkl. Fahrzeit (DB)
        monthly_hours_on_timesheets = 0.0  # Stunden die auf PDF erscheinen
        monthly_travel_hours = 0.0  # Gesamte Fahrzeit
        monthly_travel_hours_on_timesheets = 0.0  # Fahrzeit die auf PDF erscheint
        has_entries_in_month = False
        
        for e in entries:
            try:
                e_date = e.get("date") if isinstance(e, dict) else e.date
                if _date_in_year_month(e_date, year, mon):
                    has_entries_in_month = True
                    entry_obj = e if isinstance(e, dict) else e.model_dump()
                    te = TimeEntry(**entry_obj)
                    
                    user = users_by_id.get(user_id, {})
                    weekly_hours = user.get("weekly_hours", 40.0)
                    hours_per_day = weekly_hours / 5.0  # Hours per working day
                    
                    # Check for absence (Urlaub, Krankheit, Feiertag)
                    if te.absence_type and te.absence_type in ["urlaub", "krankheit", "feiertag"]:
                        # Absence days count as full working day hours (only for approved timesheets)
                        absence_hours = hours_per_day
                        monthly_total_hours += absence_hours
                        monthly_hours_on_timesheets += 0.0  # Absence doesn't appear as hours on timesheet
                    else:
                        # Calculate all hours (always includes travel time for DB)
                        total_entry_hours = _entry_hours(te)
                        monthly_total_hours += total_entry_hours
                        
                        # Calculate hours that appear on timesheet (only if include_travel_time=True)
                        hours_on_timesheet = 0.0
                        if te.start_time and te.end_time:
                            try:
                                sh, sm = map(int, te.start_time.split(":"))
                                eh, em = map(int, te.end_time.split(":"))
                                start = sh * 60 + sm
                                end = eh * 60 + em
                                worked = max(0, end - start - int(te.break_minutes))
                                hours_on_timesheet = max(0.0, worked / 60.0)
                            except Exception:
                                pass
                        
                        # Add travel time to timesheet hours only if checkbox is checked
                        travel_hours = (te.travel_time_minutes or 0) / 60.0
                        monthly_travel_hours += travel_hours
                        
                        if te.include_travel_time and travel_hours > 0:
                            hours_on_timesheet += travel_hours
                            monthly_travel_hours_on_timesheets += travel_hours
                        
                        monthly_hours_on_timesheets += hours_on_timesheet
                    
            except Exception:
                continue
        
        # Track this timesheet if it has entries in the month
        if has_entries_in_month:
            timesheets_by_user[user_id].add(timesheet_id)
        
        # Add hours to user stats – nur unterschriebene (hochgeladene) UND freigegebene Stundenzettel zählen
        timesheet_status = t.get("status", "draft")
        if (
            timesheet_status == "approved"
            and t.get("signed_pdf_path")
            and (monthly_total_hours > 0 or has_entries_in_month)
        ):
            user_stats[user_id]["total_hours"] += monthly_total_hours
            user_stats[user_id]["hours_on_timesheets"] += monthly_hours_on_timesheets
            user_stats[user_id]["travel_hours"] += monthly_travel_hours
            user_stats[user_id]["travel_hours_on_timesheets"] += monthly_travel_hours_on_timesheets
    
    # Aggregate travel expenses per user for the month
    for expense in travel_expenses:
        user_id = expense.get("user_id")
        expense_status = expense.get("status", "draft")
        
        # Only count approved expenses
        if expense_status == "approved":
            if user_id not in user_stats:
                # Initialize if user has expenses but no timesheets
                user_name = expense.get("user_name", "")
                user_stats[user_id] = {
                    "user_name": user_name,
                    "total_hours": 0.0,
                    "hours_on_timesheets": 0.0,
                    "travel_hours": 0.0,
                    "travel_hours_on_timesheets": 0.0,
                    "travel_kilometers": 0.0,
                    "travel_expenses": 0.0,
                    "timesheets_count": 0
                }
            
            user_stats[user_id]["travel_kilometers"] += expense.get("kilometers", 0.0)
            user_stats[user_id]["travel_expenses"] += expense.get("expenses", 0.0)
    
    # Set timesheets count from tracked sets
    for user_id in user_stats:
        user_stats[user_id]["timesheets_count"] = len(timesheets_by_user.get(user_id, set()))

    stats: List[AccountingMonthlyStat] = []
    for uid, data in user_stats.items():
        stats.append(AccountingMonthlyStat(
            user_id=uid,
            user_name=data["user_name"],
            month=month,
            total_hours=round(data["total_hours"], 2),
            hours_on_timesheets=round(data["hours_on_timesheets"], 2),
            travel_hours=round(data["travel_hours"], 2),
            travel_kilometers=round(data.get("travel_kilometers", 0.0), 2),
            travel_expenses=round(data.get("travel_expenses", 0.0), 2),
            travel_hours_on_timesheets=round(data["travel_hours_on_timesheets"], 2),
            timesheets_count=data["timesheets_count"]
        ))

    # Sort by user_name
    stats.sort(key=lambda s: s.user_name.lower())
    return AccountingStatsResponse(month=month, stats=stats)

@api_router.get("/accounting/timesheets-list")
async def get_accounting_timesheets_list(
    month: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_accounting_or_admin_user)
):
    """Get list of all timesheets for accounting (can filter by month/user)"""
    query = {}
    
    if month:
        try:
            year, mon = map(int, month.split("-"))
            # Find timesheets that have entries in this month
            query["week_start"] = {
                "$gte": datetime(year, mon, 1).strftime("%Y-%m-%d"),
                "$lte": (datetime(year, mon + 1, 1) - timedelta(days=1)).strftime("%Y-%m-%d") if mon < 12 
                else (datetime(year + 1, 1, 1) - timedelta(days=1)).strftime("%Y-%m-%d")
            }
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
    
    if user_id:
        query["user_id"] = user_id
    
    timesheets = await db.timesheets.find(query).to_list(1000)
    
    # Remove MongoDB internal id and build models
    sanitized = []
    for t in timesheets:
        t.pop("_id", None)
        sanitized.append(WeeklyTimesheet(**t))
    
    return sanitized

@api_router.post("/timesheets/{timesheet_id}/approve")
async def approve_timesheet(timesheet_id: str, current_user: User = Depends(get_accounting_or_admin_user)):
    """Approve a timesheet - nur in Ausnahmefällen durch Buchhaltung/Admin.
    
    Normalfall: Agent genehmigt automatisch, wenn Unterschrift verifiziert wurde.
    Buchhaltung kann nur genehmigen, wenn:
    - signed_pdf_verified=False (Agent konnte Unterschrift nicht verifizieren)
    - oder nur Abwesenheitstage (Urlaub/Krankheit/Feiertag) ohne Arbeitszeit
    """
    # Find timesheet
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Nur sent oder draft Stundenzettel können genehmigt werden
    if timesheet["status"] not in ["sent", "draft"]:
        raise HTTPException(status_code=400, detail="Only sent or draft timesheets can be approved")
    
    # Prüfe, ob bereits automatisch genehmigt wurde (sollte nicht vorkommen)
    if timesheet.get("signed_pdf_verified") and timesheet.get("status") == "approved":
        raise HTTPException(
            status_code=400,
            detail="Timesheet wurde bereits automatisch durch Agent genehmigt. Keine manuelle Genehmigung erforderlich."
        )
    
    # Normalfall: Wenn Unterschrift verifiziert wurde, sollte automatisch approved sein
    # Manuelle Genehmigung nur in Ausnahmefällen:
    # 1. signed_pdf_verified=False (Agent konnte nicht verifizieren)
    # 2. Nur Abwesenheitstage (Urlaub/Krankheit/Feiertag) ohne Arbeitszeit
    signed_pdf_verified = timesheet.get("signed_pdf_verified", False)
    has_signed_pdf = bool(timesheet.get("signed_pdf_path"))
    
    # Prüfe, ob nur Abwesenheitstage vorhanden sind
    entries = timesheet.get("entries", [])
    only_absences = True
    if entries:
        ABSENCE_TYPES = {"urlaub", "krankheit", "feiertag"}
        for entry in entries:
            absence_type = entry.get("absence_type") if isinstance(entry, dict) else getattr(entry, "absence_type", None)
            has_work_time = bool(entry.get("start_time") if isinstance(entry, dict) else getattr(entry, "start_time", None))
            if not absence_type or absence_type.lower() not in ABSENCE_TYPES or has_work_time:
                only_absences = False
                break
    else:
        only_absences = False
    
    # Genehmigung nur in Ausnahmefällen:
    # - Unterschrift nicht verifiziert ODER nur Abwesenheitstage
    if signed_pdf_verified and not only_absences:
        raise HTTPException(
            status_code=400,
            detail="Dieser Stundenzettel sollte automatisch durch den Agent genehmigt werden. Bitte laden Sie den unterschriebenen Stundenzettel hoch, damit der Agent prüfen kann."
        )
    
    # Update status to approved
    await db.timesheets.update_one(
        {"id": timesheet_id},
        {"$set": {"status": "approved"}}
    )
    
    return {
        "message": "Timesheet approved successfully (Ausnahmefall)",
        "reason": "Manuelle Genehmigung durch Buchhaltung" if not signed_pdf_verified else "Nur Abwesenheitstage"
    }

@api_router.post("/timesheets/{timesheet_id}/reject")
async def reject_timesheet(timesheet_id: str, current_user: User = Depends(get_accounting_or_admin_user)):
    """Reject an approved timesheet (set back to sent)"""
    # Find timesheet
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Only approved timesheets can be rejected
    if timesheet["status"] != "approved":
        raise HTTPException(status_code=400, detail="Only approved timesheets can be rejected")
    
    # Set status back to sent
    await db.timesheets.update_one(
        {"id": timesheet_id},
        {"$set": {"status": "sent"}}
    )
    
    return {"message": "Timesheet rejected successfully"}

@api_router.get("/accounting/monthly-report-pdf")
async def get_accounting_monthly_report_pdf(
    month: str,
    request: Request,
    current_user: User = Depends(get_accounting_or_admin_user)
):
    """
    Generate PDF report for accounting monthly statistics.
    Cyber-Security: Referrer-Check und Origin-Validation.
    """
    # Cyber-Security: Referrer-Check
    referer = request.headers.get("referer", "")
    origin = request.headers.get("origin", "")
    
    allowed_origins = CORS_ORIGINS
    if origin and not any(allowed in origin for allowed in allowed_origins):
        if referer and not any(allowed in referer for allowed in allowed_origins):
            logging.warning(f"Blocked PDF download - invalid origin/referer: {origin}/{referer}")
            raise HTTPException(status_code=403, detail="Access denied: Invalid origin")
    
    # Get statistics
    stats_response = await get_accounting_monthly_stats(month, current_user)
    
    # Generate PDF
    pdf_bytes = generate_accounting_report_pdf(stats_response)
    
    # Generate filename
    month_date = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    month_name = month_date.strftime("%Y-%m")
    filename = f"Buchhaltungsbericht_{month_name}.pdf"
    
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@api_router.post("/timesheets", response_model=WeeklyTimesheet)
async def create_timesheet(timesheet_create: WeeklyTimesheetCreate, current_user: User = Depends(get_current_user)):
    # Calculate week end (Sunday)
    from datetime import datetime, timedelta
    week_start = datetime.strptime(timesheet_create.week_start, "%Y-%m-%d")
    week_end = week_start + timedelta(days=6)
    vehicle_cache: Dict[str, Dict[str, Any]] = {}
    selected_week_vehicle_id: Optional[str] = None
    
    if timesheet_create.week_vehicle_id:
        vehicle = await ensure_vehicle_access(timesheet_create.week_vehicle_id, current_user.id, db)
        vehicle_cache[timesheet_create.week_vehicle_id] = vehicle
        selected_week_vehicle_id = timesheet_create.week_vehicle_id
    
    for entry in timesheet_create.entries:
        if entry.vehicle_id:
            if entry.vehicle_id not in vehicle_cache:
                vehicle = await ensure_vehicle_access(entry.vehicle_id, current_user.id, db)
                vehicle_cache[entry.vehicle_id] = vehicle
    
    # Automatisch genehmigte Urlaubstage hinzufügen
    entries_with_vacation = await add_vacation_entries_to_timesheet(
        timesheet_create.entries,
        timesheet_create.week_start,
        week_end.strftime("%Y-%m-%d"),
        current_user.id,
        db
    )
    
    processed_entries: List[TimeEntry] = []
    for entry in entries_with_vacation:
        entry_vehicle_id = entry.vehicle_id or selected_week_vehicle_id
        if entry_vehicle_id and entry_vehicle_id not in vehicle_cache:
            vehicle = await ensure_vehicle_access(entry_vehicle_id, current_user.id, db)
            vehicle_cache[entry_vehicle_id] = vehicle
        entry_dict = entry.model_dump()
        entry_dict["vehicle_id"] = entry_vehicle_id
        processed_entries.append(TimeEntry(**entry_dict))
    
    timesheet = WeeklyTimesheet(
        user_id=current_user.id,
        user_name=current_user.name,
        week_start=timesheet_create.week_start,
        week_end=week_end.strftime("%Y-%m-%d"),
        week_vehicle_id=selected_week_vehicle_id,
        entries=processed_entries
    )
    
    await db.timesheets.insert_one(timesheet.dict())
    return timesheet

@api_router.get("/timesheets", response_model=List[WeeklyTimesheet])
async def get_timesheets(current_user: User = Depends(get_current_user)):
    if current_user.can_view_all_data():
        timesheets = await db.timesheets.find().to_list(1000)
    else:
        timesheets = await db.timesheets.find({"user_id": current_user.id}).to_list(1000)
    
    # Remove Mongo _id and build models
    sanitized = []
    for t in timesheets:
        t.pop("_id", None)
        sanitized.append(WeeklyTimesheet(**t))
    return sanitized

@api_router.put("/timesheets/{timesheet_id}", response_model=WeeklyTimesheet)
async def update_timesheet(timesheet_id: str, timesheet_update: TimesheetUpdate, current_user: User = Depends(get_current_user)):
    # Find timesheet
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check permissions (admin/accounting can edit any, user can edit their own)
    if not current_user.can_view_all_data() and timesheet["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Prepare update data
    update_data = {}
    if timesheet_update.week_start:
        # Calculate new week end
        from datetime import datetime, timedelta
        week_start = datetime.strptime(timesheet_update.week_start, "%Y-%m-%d")
        week_end = week_start + timedelta(days=6)
        update_data["week_start"] = timesheet_update.week_start
        update_data["week_end"] = week_end.strftime("%Y-%m-%d")
    
    vehicle_cache: Dict[str, Dict[str, Any]] = {}
    week_vehicle_id = timesheet.get("week_vehicle_id")
    if "week_vehicle_id" in timesheet_update.__fields_set__:
        if timesheet_update.week_vehicle_id:
            await ensure_vehicle_access(timesheet_update.week_vehicle_id, timesheet["user_id"], db)
            week_vehicle_id = timesheet_update.week_vehicle_id
            update_data["week_vehicle_id"] = week_vehicle_id
        else:
            week_vehicle_id = None
            update_data["week_vehicle_id"] = None
    elif week_vehicle_id:
        # Ensure existing cached vehicle if needed later
        vehicle_cache[week_vehicle_id] = await ensure_vehicle_access(week_vehicle_id, timesheet["user_id"], db)
    
    if timesheet_update.entries is not None:
        # Automatisch genehmigte Urlaubstage hinzufügen
        week_start_str = update_data.get("week_start", timesheet.get("week_start"))
        week_end_str = update_data.get("week_end", timesheet.get("week_end"))
        
        # Validate provided vehicle assignments
        if week_vehicle_id and week_vehicle_id not in vehicle_cache:
            vehicle_cache[week_vehicle_id] = await ensure_vehicle_access(week_vehicle_id, timesheet["user_id"], db)
        
        for entry in timesheet_update.entries:
            if entry.vehicle_id:
                if entry.vehicle_id not in vehicle_cache:
                    vehicle_cache[entry.vehicle_id] = await ensure_vehicle_access(entry.vehicle_id, timesheet["user_id"], db)
        
        entries_with_vacation = await add_vacation_entries_to_timesheet(
            timesheet_update.entries,
            week_start_str,
            week_end_str,
            timesheet["user_id"],
            db
        )
        processed_entries: List[Dict[str, Any]] = []
        for entry in entries_with_vacation:
            entry_vehicle_id = entry.vehicle_id or week_vehicle_id
            if entry_vehicle_id and entry_vehicle_id not in vehicle_cache:
                vehicle_cache[entry_vehicle_id] = await ensure_vehicle_access(entry_vehicle_id, timesheet["user_id"], db)
            entry_dict = entry.model_dump()
            entry_dict["vehicle_id"] = entry_vehicle_id
            processed_entries.append(entry_dict)
        update_data["entries"] = processed_entries
    
    if timesheet_update.signed_pdf_verification_notes is not None or timesheet_update.signed_pdf_verified is not None:
        if not current_user.can_view_all_data():
            raise HTTPException(status_code=403, detail="Nur Buchhaltung oder Admin können Prüfbemerkungen bearbeiten")
        if timesheet_update.signed_pdf_verification_notes is not None:
            update_data["signed_pdf_verification_notes"] = timesheet_update.signed_pdf_verification_notes
        if timesheet_update.signed_pdf_verified is not None:
            update_data["signed_pdf_verified"] = timesheet_update.signed_pdf_verified
    
    if update_data:
        await db.timesheets.update_one({"id": timesheet_id}, {"$set": update_data})
    
    updated_timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not updated_timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found after update")
    
    updated_timesheet.pop("_id", None)
    return WeeklyTimesheet(**updated_timesheet)

@api_router.delete("/timesheets/{timesheet_id}")
async def delete_timesheet(timesheet_id: str, current_user: User = Depends(get_current_user)):
    # Find timesheet
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check permissions (admin/accounting can delete any, user can delete their own)
    if not current_user.can_view_all_data() and timesheet["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if timesheet status allows deletion (only "draft" can be deleted)
    if timesheet["status"] != "draft":
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete timesheet that has been sent. Only draft timesheets can be deleted."
        )
    
    # Delete timesheet
    await db.timesheets.delete_one({"id": timesheet_id})
    
    return {"message": "Timesheet deleted successfully"}

@api_router.get("/timesheets/{timesheet_id}/pdf")
async def get_timesheet_pdf(
    timesheet_id: str, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Download PDF - Nur für authentifizierte Benutzer, keine direkten Links.
    Cyber-Security: Referrer-Check und Origin-Validation.
    """
    # Cyber-Security: Referrer-Check (muss von erlaubter Domain kommen)
    referer = request.headers.get("referer", "")
    origin = request.headers.get("origin", "")
    
    # Erlaubte Origins aus CORS-Konfiguration
    allowed_origins = CORS_ORIGINS
    if origin and not any(allowed in origin for allowed in allowed_origins):
        if referer and not any(allowed in referer for allowed in allowed_origins):
            logging.warning(f"Blocked PDF download - invalid origin/referer: {origin}/{referer}")
            raise HTTPException(status_code=403, detail="Access denied: Invalid origin")
    
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check permissions
    if not current_user.is_admin and timesheet["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Remove MongoDB internal id for model creation
    timesheet.pop("_id", None)
    timesheet_obj = WeeklyTimesheet(**timesheet)
    pdf_bytes = generate_timesheet_pdf(timesheet_obj)
    
    # Generate new filename format
    filename = await generate_pdf_filename(timesheet_obj, timesheet_obj.user_name)
    
    # Cyber-Security: Keine direkten Links - Download nur über API
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store, no-cache, must-revalidate",  # Verhindert Caching
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@api_router.post("/timesheets/{timesheet_id}/download-and-email")
async def download_and_email_timesheet(
    timesheet_id: str, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Download PDF and automatically send copy to admin.
    Cyber-Security: Referrer-Check und Origin-Validation.
    """
    # Cyber-Security: Referrer-Check
    referer = request.headers.get("referer", "")
    origin = request.headers.get("origin", "")
    
    allowed_origins = CORS_ORIGINS
    if origin and not any(allowed in origin for allowed in allowed_origins):
        if referer and not any(allowed in referer for allowed in allowed_origins):
            logging.warning(f"Blocked PDF download - invalid origin/referer: {origin}/{referer}")
            raise HTTPException(status_code=403, detail="Access denied: Invalid origin")
    
    # Get timesheet
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check permissions
    if not current_user.is_admin and timesheet["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    timesheet_obj = WeeklyTimesheet(**timesheet)
    pdf_bytes = generate_timesheet_pdf(timesheet_obj)
    
    # Generate new filename format
    filename = await generate_pdf_filename(timesheet_obj, timesheet_obj.user_name)
    
    # Send email copy to admin (if SMTP configured)
    try:
        smtp_config = await db.smtp_config.find_one()
        if smtp_config:
            # Send email with PDF attachment
            msg = MIMEMultipart()
            msg['From'] = smtp_config["smtp_username"]
            msg['To'] = current_user.email
            msg['Cc'] = smtp_config["admin_email"]
            msg['Subject'] = f"Stundenzettel Download - {timesheet_obj.user_name} - {get_calendar_week(timesheet_obj.week_start)}"
            
            body = f"""
            Hallo {current_user.name},
            
            Sie haben den Stundenzettel für die Woche vom {timesheet_obj.week_start} bis {timesheet_obj.week_end} heruntergeladen.
            Eine Kopie wurde automatisch an die Admin-Adresse gesendet.
            
            Dateiname: {filename}
            
            Mit freundlichen Grüßen
            {COMPANY_INFO["name"]}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Attach PDF with new filename
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={filename}'
            )
            msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"])
            server.starttls()
            server.login(smtp_config["smtp_username"], smtp_config["smtp_password"])
            
            recipients = [current_user.email, smtp_config["admin_email"]]
            text = msg.as_string()
            server.sendmail(smtp_config["smtp_username"], recipients, text.encode('utf-8'))
            server.quit()
            
            print(f"Email sent successfully to {recipients}")
            
            # Update timesheet status to "sent" after successful email
            await db.timesheets.update_one(
                {"id": timesheet_id},
                {"$set": {"status": "sent"}}
            )
    
    except Exception as e:
        print(f"Email sending failed (continuing with download): {str(e)}")
        # Continue with download even if email fails
    
    # Return PDF for download with new filename
    # Cyber-Security: Keine direkten Links - Download nur über API
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@api_router.post("/timesheets/{timesheet_id}/send-email")
async def send_timesheet_email(timesheet_id: str, current_user: User = Depends(get_current_user)):
    # Get timesheet
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check permissions
    if not current_user.is_admin and timesheet["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get SMTP config
    smtp_config = await db.smtp_config.find_one()
    if not smtp_config:
        raise HTTPException(status_code=400, detail="SMTP configuration not found. Please contact admin.")
    
    timesheet.pop("_id", None)
    timesheet_obj = WeeklyTimesheet(**timesheet)
    pdf_bytes = generate_timesheet_pdf(timesheet_obj)
    
    # Send email
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_config["smtp_username"]
        msg['To'] = current_user.email
        msg['Cc'] = smtp_config["admin_email"]
        msg['Subject'] = f"Stundenzettel - {timesheet_obj.user_name} - Woche {timesheet_obj.week_start}"
        
        body = f"""
        Hallo {timesheet_obj.user_name},
        
        anbei finden Sie Ihren Stundenzettel für die Woche vom {timesheet_obj.week_start} bis {timesheet_obj.week_end}.
        
        Mit freundlichen Grüßen
        {COMPANY_INFO["name"]}
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Attach PDF with new filename
        filename = await generate_pdf_filename(timesheet_obj, timesheet_obj.user_name)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={filename}'
        )
        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"])
        server.starttls()
        server.login(smtp_config["smtp_username"], smtp_config["smtp_password"])
        
        recipients = [current_user.email, smtp_config["admin_email"]]
        text = msg.as_string()
        server.sendmail(smtp_config["smtp_username"], recipients, text.encode('utf-8'))
        server.quit()
        
        # Update timesheet status to "sent" regardless of email success
        # (User initiated send action, so we mark it as sent)
        await db.timesheets.update_one(
            {"id": timesheet_id},
            {"$set": {"status": "sent"}}
        )
        
        return {"message": "Email sent successfully"}
    
    except Exception as e:
        # Even if email fails, mark as sent since user initiated the action
        await db.timesheets.update_one(
            {"id": timesheet_id},
            {"$set": {"status": "sent"}}
        )
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@limiter.limit("10/hour")  # Max 10 Uploads pro Stunde
@api_router.post("/timesheets/{timesheet_id}/upload-signed")
async def upload_signed_timesheet(
    request: Request,
    timesheet_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload unterschriebener Stundenzettel-PDF (vom Kunden unterzeichnet, vom User hochgeladen).
    
    Der Dokumenten-Agent prüft automatisch die Unterschrift:
    - Wenn Unterschrift verifiziert: Stundenzettel wird automatisch als "approved" markiert und Arbeitszeit gutgeschrieben
    - Wenn Unterschrift nicht verifiziert: Status bleibt "sent" für manuelle Prüfung durch Buchhaltung
    
    Benachrichtigt alle Buchhaltungs-User per E-Mail (unterscheidet zwischen automatisch genehmigt und manuelle Prüfung erforderlich).
    """
    
    # Get timesheet
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Stundenzettel nicht gefunden")
    
    # Check permissions - nur der Owner kann unterschriebene Version hochladen
    if timesheet["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Nur der Eigentümer kann den unterschriebenen Stundenzettel hochladen")
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien sind erlaubt")
    
    # Read file contents
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Datei ist leer")
    
    # Validate file size (max 10MB)
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Datei zu groß (max 10MB)")
    
    # Create safe filename
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
    if not safe_filename:
        safe_filename = f"unterschrieben_{timesheet_id}.pdf"
    
    # Erstelle eindeutigen Ordner pro Stundenzettel: User_Woche_TimesheetID
    user_name_safe = re.sub(r'[^\w\-_]', '_', timesheet.get("user_name", "Unknown"))
    week_start = timesheet.get("week_start", "unknown")
    # Ordner-Name: User_Woche_TimesheetID (z.B. Max_Mustermann_2025-01-01_abc123)
    timesheet_folder = f"{user_name_safe}_{week_start}_{timesheet_id}"
    timesheet_folder_path = Path(LOCAL_RECEIPTS_PATH) / "stundenzettel" / timesheet_folder
    
    # Erstelle Ordner falls nicht vorhanden
    timesheet_folder_path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timesheet_id}_signed_{timestamp}_{safe_filename}"
    local_file_path = timesheet_folder_path / filename
    
    try:
        # Save file to local storage (DSGVO-compliant)
        with open(local_file_path, 'wb') as f:
            f.write(contents)
        
        # DSGVO Art. 32: Encrypt sensitive data
        data_encryption.encrypt_file(local_file_path)
        
        # Verify file is encrypted
        try:
            data_encryption.decrypt_file(local_file_path)
        except Exception as e:
            logging.error(f"File encryption verification failed: {e}")
            local_file_path.unlink()
            raise HTTPException(status_code=500, detail="Verschlüsselung fehlgeschlagen")
        
        # Verifiziere unterschriebenes PDF mit Dokumenten-Agent (Heuristik basierend auf PDF-Text)
        # Wenn Agent Unterschrift verifiziert, wird automatisch als Arbeitszeit gutgeschrieben (approved)
        try:
            from agents import DocumentAgent, OllamaLLM
            llm = OllamaLLM()
            doc_agent = DocumentAgent(llm)
            # Extrahiere Text (mit Entschlüsselung)
            pdf_text = doc_agent.extract_pdf_text(str(local_file_path), encryption=data_encryption)
            import re as _re
            verified = False
            notes = ""
            if pdf_text and isinstance(pdf_text, str):
                if _re.search(r"(unterschrift|unterzeichnet|signature|signed)", pdf_text, _re.IGNORECASE):
                    verified = True
                    notes = "Schlüsselwörter für Unterschrift im PDF-Text gefunden. Automatisch als Arbeitszeit gutgeschrieben."
                else:
                    notes = "Keine offensichtlichen Unterschrifts-Schlüsselwörter im PDF-Text gefunden. Manuelle Prüfung durch Buchhaltung erforderlich."
            else:
                notes = "Kein Text extrahiert. Manuelle Prüfung durch Buchhaltung erforderlich."
        except Exception as e:
            verified = False
            notes = f"Automatische Verifikation fehlgeschlagen: {str(e)}. Manuelle Prüfung durch Buchhaltung erforderlich."

        # Automatische Genehmigung, wenn Agent Unterschrift verifiziert hat
        # Buchhaltung kann nur in Ausnahmefällen genehmigen (wenn verified=False)
        new_status = "approved" if verified else "sent"
        
        # Update timesheet with signed PDF metadata
        await db.timesheets.update_one(
            {"id": timesheet_id},
            {
                "$set": {
                    "signed_pdf_path": str(local_file_path),
                    "signed_pdf_verified": bool(verified),
                    "signed_pdf_verification_notes": notes,
                    "status": new_status  # Automatisch approved wenn verifiziert, sonst sent für manuelle Prüfung
                }
            }
        )
        
        # Audit log
        audit_logger.log_access(
            action="upload_signed_timesheet",
            user_id=current_user.id,
            resource_type="timesheet",
            resource_id=timesheet_id,
            details={"filename": safe_filename, "local_path": str(local_file_path), "encrypted": True}
        )

        # Push-Benachrichtigung an Buchhaltung
        try:
            await notify_role(
                role="accounting",
                title="Unterschriebener Stundenzettel hochgeladen",
                body=f"{timesheet.get('user_name', 'User')} Woche {timesheet.get('week_start', '')}",
                data={"type": "timesheet_signed_upload", "timesheet_id": timesheet_id}
            )
        except Exception as e:
            logging.warning(f"Push notify (timesheet upload) failed: {e}")
        
        # Get all accounting users
        accounting_users = await db.users.find({"role": "accounting"}).to_list(100)
        
        # Send email to all accounting users
        smtp_config = await db.smtp_config.find_one()
        if smtp_config and accounting_users:
            try:
                timesheet_obj = WeeklyTimesheet(**timesheet)
                week_info = f"KW {get_calendar_week(timesheet_obj.week_start)} ({timesheet_obj.week_start} - {timesheet_obj.week_end})"
                
                # Prepare email
                msg = MIMEMultipart()
                if verified:
                    subject = f"Stundenzettel automatisch genehmigt - {timesheet_obj.user_name} - {week_info}"
                else:
                    subject = f"Unterschriebener Stundenzettel - Manuelle Prüfung erforderlich - {timesheet_obj.user_name} - {week_info}"
                msg['From'] = smtp_config["smtp_username"]
                msg['Subject'] = subject
                
                if verified:
                    body = f"""Hallo,

ein unterschriebener Stundenzettel wurde hochgeladen und automatisch durch den Agent genehmigt:

Mitarbeiter: {timesheet_obj.user_name}
Woche: {week_info}
Stundenzettel-ID: {timesheet_id}
Status: Automatisch genehmigt (Unterschrift verifiziert)

Der unterschriebene Stundenzettel wurde verschlüsselt im lokalen Speicher gespeichert.
Die Arbeitszeit wurde automatisch gutgeschrieben.

Mit freundlichen Grüßen
{COMPANY_INFO["name"]}
                """
                else:
                    body = f"""Hallo,

ein unterschriebener Stundenzettel wurde hochgeladen, benötigt aber manuelle Prüfung:

Mitarbeiter: {timesheet_obj.user_name}
Woche: {week_info}
Stundenzettel-ID: {timesheet_id}
Status: Manuelle Prüfung erforderlich

Der Agent konnte die Unterschrift nicht automatisch verifizieren.
Bitte prüfen Sie den Stundenzettel im System und genehmigen Sie ihn manuell, falls die Unterschrift vorhanden ist.

Mit freundlichen Grüßen
{COMPANY_INFO["name"]}
                """
                
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # Send to all accounting users
                recipients = [user["email"] for user in accounting_users]
                msg['To'] = ", ".join(recipients)
                
                server = smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"])
                server.starttls()
                server.login(smtp_config["smtp_username"], smtp_config["smtp_password"])
                server.sendmail(smtp_config["smtp_username"], recipients, msg.as_string().encode('utf-8'))
                server.quit()
                
                logging.info(f"Email sent to accounting users: {recipients}")
                
            except Exception as e:
                logging.error(f"Failed to send email to accounting users: {e}")
                # Don't fail the upload if email fails
        
        return {
            "message": "Unterschriebener Stundenzettel erfolgreich hochgeladen",
            "filename": safe_filename,
            "accounting_users_notified": len(accounting_users) if accounting_users else 0
        }
        
    except Exception as e:
        if local_file_path.exists():
            local_file_path.unlink()
        logging.error(f"Failed to upload signed timesheet: {e}")
        raise HTTPException(status_code=500, detail=f"Upload fehlgeschlagen: {str(e)}")

@api_router.post("/admin/smtp-config")
async def update_smtp_config(smtp_config: SMTPConfigCreate, current_user: User = Depends(get_admin_user)):
    # Delete existing config
    await db.smtp_config.delete_many({})
    
    # Create new config
    config = SMTPConfig(**smtp_config.dict())
    await db.smtp_config.insert_one(config.dict())
    
    return {"message": "SMTP configuration updated successfully"}

@api_router.get("/admin/smtp-config")
async def get_smtp_config(current_user: User = Depends(get_admin_user)):
    config = await db.smtp_config.find_one()
    if not config:
        return None
    
    # Don't return password and remove MongoDB ObjectId
    config_safe = {k: v for k, v in config.items() if k not in ["smtp_password", "_id"]}
    return config_safe

# Initialize admin user and compliance on startup
@app.on_event("startup")
async def startup_tasks():
    """Startup tasks: create admin user and setup compliance"""
    await create_admin_user()
    await ensure_test_announcement()
    logger.info("DSGVO Compliance: Retention manager initialized")
    logger.info("EU-AI-Act Compliance: AI transparency logging enabled")

async def ensure_test_announcement():
    existing = await db.announcements.find_one({"title": TEST_ANNOUNCEMENT_TITLE})
    if existing:
        return False
    announcement = Announcement(
        title=TEST_ANNOUNCEMENT_TITLE,
        content=TEST_ANNOUNCEMENT_CONTENT,
        active=True,
        created_by="system"
    )
    announcement_dict = announcement.model_dump()
    announcement_dict["created_at"] = datetime.utcnow()
    announcement_dict["updated_at"] = datetime.utcnow()
    await db.announcements.insert_one(announcement_dict)
    logger.info("Test announcement created for verification.")
    return True

async def create_admin_user(email: Optional[str] = None, reset_if_exists: bool = False):
    target_email = (email or DEFAULT_ADMIN_EMAIL).strip().lower()
    admin = await db.users.find_one({"email": target_email})
    if admin:
        if reset_if_exists:
            # Reset admin user: new secret, disable 2FA, reset password
            two_fa_secret = pyotp.random_base32()
            await db.users.update_one(
                {"email": target_email},
                {
                    "$set": {
                        "two_fa_secret": two_fa_secret,
                        "two_fa_enabled": False,
                        "hashed_password": get_password_hash(DEFAULT_ADMIN_PASSWORD),
                        "name": DEFAULT_ADMIN_NAME,
                        "role": "admin",
                        "is_admin": True
                    }
                }
            )
            logger.info(f"Admin user reset: {target_email} / {DEFAULT_ADMIN_PASSWORD} (2FA pending)")
            return True
        return False
    two_fa_secret = pyotp.random_base32()
    admin_user = User(
        email=target_email,
        name=DEFAULT_ADMIN_NAME,
        role="admin",
        hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
        two_fa_secret=two_fa_secret,
        two_fa_enabled=False
    )
    admin_dict = admin_user.model_dump()
    admin_dict["is_admin"] = True
    await db.users.insert_one(admin_dict)
    logger.info(f"Admin user created: {target_email} / {DEFAULT_ADMIN_PASSWORD} (2FA pending)")
    return True

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy (CSP) - Anpassen je nach Bedarf
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # unsafe-inline/eval nur wenn nötig
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # HTTPS Strict Transport Security (HSTS) - nur wenn HTTPS aktiv
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        return response

# HTTPS Redirect Middleware (nur in Produktion)
class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Nur in Produktion umleiten (nicht bei localhost)
        if os.getenv("ENFORCE_HTTPS", "false").lower() == "true":
            if request.url.scheme == "http" and "localhost" not in str(request.url.hostname):
                from starlette.responses import RedirectResponse
                url = str(request.url).replace("http://", "https://", 1)
                return RedirectResponse(url=url, status_code=301)
        return await call_next(request)

# Include router
app.include_router(api_router)

# Middleware-Reihenfolge ist wichtig: Security Headers zuletzt
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS-Konfiguration aus Umgebungsvariablen
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "https://app.byte-commander.de,http://localhost:3000,http://localhost:8000,http://192.168.178.150,http://192.168.178.151"
).split(",")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,  # Aus Sicherheitsgründen: Keine Credentials über CORS
    allow_origins=CORS_ORIGINS,  # Nur erlaubte Origins aus .env
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explizite Methoden, nicht "*"
    allow_headers=["Content-Type", "Authorization"],  # Explizite Headers, nicht "*"
    expose_headers=["X-Request-ID"],  # Nur notwendige Headers exponieren
    max_age=3600,  # Preflight-Cache: 1 Stunde
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Travel Expenses endpoints
@api_router.get("/travel-expenses", response_model=List[TravelExpense])
async def get_travel_expenses(current_user: User = Depends(get_current_user)):
    """Get travel expenses for current user, or all if admin/accounting"""
    query = {}
    if not current_user.can_view_all_data():
        query["user_id"] = current_user.id
    
    expenses = []
    async for expense in db.travel_expenses.find(query):
        expenses.append(TravelExpense(**expense))
    
    return sorted(expenses, key=lambda x: x.date, reverse=True)

@api_router.post("/travel-expenses", response_model=TravelExpense)
async def create_travel_expense(expense_create: TravelExpenseCreate, current_user: User = Depends(get_current_user)):
    """Create a new travel expense"""
    expense = TravelExpense(
        user_id=current_user.id,
        user_name=current_user.name,
        date=expense_create.date,
        description=expense_create.description,
        kilometers=expense_create.kilometers,
        expenses=expense_create.expenses,
        customer_project=expense_create.customer_project
    )
    
    expense_dict = expense.model_dump()
    expense_dict["created_at"] = datetime.utcnow()
    await db.travel_expenses.insert_one(expense_dict)
    
    return expense

@api_router.put("/travel-expenses/{expense_id}", response_model=TravelExpense)
async def update_travel_expense(
    expense_id: str,
    expense_update: TravelExpenseUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a travel expense"""
    expense = await db.travel_expenses.find_one({"id": expense_id})
    if not expense:
        raise HTTPException(status_code=404, detail="Travel expense not found")
    
    # Check permissions
    if not current_user.can_view_all_data() and expense["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Only allow updates if status is draft
    if expense.get("status") != "draft" and not current_user.can_view_all_data():
        raise HTTPException(status_code=400, detail="Can only update draft expenses")
    
    update_data = expense_update.model_dump(exclude_unset=True)
    await db.travel_expenses.update_one(
        {"id": expense_id},
        {"$set": update_data}
    )
    
    updated_expense = await db.travel_expenses.find_one({"id": expense_id})
    return TravelExpense(**updated_expense)

@api_router.delete("/travel-expenses/{expense_id}")
async def delete_travel_expense(expense_id: str, current_user: User = Depends(get_current_user)):
    """Delete a travel expense"""
    expense = await db.travel_expenses.find_one({"id": expense_id})
    if not expense:
        raise HTTPException(status_code=404, detail="Travel expense not found")
    
    # Check permissions
    if not current_user.can_view_all_data() and expense["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Only allow deletion if status is draft
    if expense.get("status") != "draft" and not current_user.can_view_all_data():
        raise HTTPException(status_code=400, detail="Can only delete draft expenses")
    
    await db.travel_expenses.delete_one({"id": expense_id})
    return {"message": "Travel expense deleted successfully"}

@api_router.post("/travel-expenses/{expense_id}/approve")
async def approve_travel_expense(expense_id: str, current_user: User = Depends(get_accounting_or_admin_user)):
    """Approve a travel expense (accounting/admin only)"""
    expense = await db.travel_expenses.find_one({"id": expense_id})
    if not expense:
        raise HTTPException(status_code=404, detail="Travel expense not found")
    
    await db.travel_expenses.update_one(
        {"id": expense_id},
        {"$set": {"status": "approved"}}
    )
    
    return {"message": "Travel expense approved successfully"}

@api_router.post("/travel-expenses/{expense_id}/reject")
async def reject_travel_expense(expense_id: str, current_user: User = Depends(get_accounting_or_admin_user)):
    """Reject an approved travel expense (accounting/admin only)"""
    expense = await db.travel_expenses.find_one({"id": expense_id})
    if not expense:
        raise HTTPException(status_code=404, detail="Travel expense not found")
    
    if expense["status"] != "approved":
        raise HTTPException(status_code=400, detail="Only approved expenses can be rejected")
    
    await db.travel_expenses.update_one(
        {"id": expense_id},
        {"$set": {"status": "sent"}}
    )
    
    return {"message": "Travel expense rejected successfully"}

# Announcements endpoints
@api_router.get("/announcements", response_model=List[Announcement])
async def get_announcements(active_only: bool = False):
    """Get all announcements (or only active ones)"""
    query = {"active": True} if active_only else {}
    announcements = []
    async for announcement in db.announcements.find(query).sort("created_at", -1):
        announcements.append(Announcement(**announcement))
    return announcements

@api_router.post("/announcements", response_model=Announcement)
async def create_announcement(
    announcement_create: AnnouncementCreate,
    current_user: User = Depends(get_admin_user)
):
    """Create a new announcement (admin only)"""
    announcement = Announcement(
        title=announcement_create.title,
        content=announcement_create.content,
        image_url=announcement_create.image_url,
        image_filename=announcement_create.image_filename,
        active=announcement_create.active,
        created_by=current_user.id
    )
    
    announcement_dict = announcement.model_dump()
    announcement_dict["created_at"] = datetime.utcnow()
    announcement_dict["updated_at"] = datetime.utcnow()
    await db.announcements.insert_one(announcement_dict)
    
    return announcement

@api_router.put("/announcements/{announcement_id}", response_model=Announcement)
async def update_announcement(
    announcement_id: str,
    announcement_update: AnnouncementUpdate,
    current_user: User = Depends(get_admin_user)
):
    """Update an announcement (admin only)"""
    announcement = await db.announcements.find_one({"id": announcement_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    update_data = announcement_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.announcements.update_one(
        {"id": announcement_id},
        {"$set": update_data}
    )
    
    updated_announcement = await db.announcements.find_one({"id": announcement_id})
    return Announcement(**updated_announcement)

@api_router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: User = Depends(get_admin_user)
):
    """Delete an announcement (admin only)"""
    result = await db.announcements.delete_one({"id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement deleted successfully"}

@api_router.post("/announcements/upload-image")
async def upload_announcement_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user)
):
    """Upload an image for announcements (admin only) - returns base64 encoded image"""
    # Check file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read file content
    contents = await file.read()
    
    # Check file size (max 5MB)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size must be less than 5MB")
    
    # Encode to base64
    import base64
    image_base64 = base64.b64encode(contents).decode('utf-8')
    
    # Create data URL
    image_url = f"data:{file.content_type};base64,{image_base64}"
    
    return {
        "image_url": image_url,
        "image_filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents)
    }

# Travel Expense Reports endpoints
# NOTE: Ollama LLM integration for automatic review is pending
@api_router.get("/travel-expense-reports", response_model=List[TravelExpenseReport])
async def get_travel_expense_reports(
    month: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get travel expense reports for current user, or all if admin/accounting"""
    query = {}
    if not current_user.can_view_all_data():
        query["user_id"] = current_user.id
    
    if month:
        query["month"] = month
    
    reports = []
    async for report in db.travel_expense_reports.find(query).sort("created_at", -1):
        reports.append(TravelExpenseReport(**report))
    
    return reports

@api_router.get("/travel-expense-reports/available-months")
async def get_available_months(current_user: User = Depends(get_current_user)):
    """Get available months for expense reports (current month + 2 months back)"""
    today = datetime.utcnow()
    months = []
    for i in range(3):  # Current + 2 months back
        month_date = today - timedelta(days=30*i)
        month_str = month_date.strftime("%Y-%m")
        months.append({
            "value": month_str,
            "label": month_date.strftime("%B %Y")
        })
    return months

@api_router.post("/travel-expense-reports/initialize/{month}")
async def initialize_expense_report(
    month: str,
    current_user: User = Depends(get_current_user)
):
    """Initialize expense report for a month - auto-fills from approved timesheets"""
    try:
        year, mon = map(int, month.split("-"))
        _ = datetime(year, mon, 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
    
    existing = await db.travel_expense_reports.find_one({
        "user_id": current_user.id,
        "month": month
    })
    if existing:
        return TravelExpenseReport(**existing)
    
    timesheets = await db.timesheets.find({
        "user_id": current_user.id,
        "status": "approved",
        "signed_pdf_path": {"$ne": None},
        "signed_pdf_verified": True
    }).to_list(1000)
    
    entries_dict = {}
    for ts in timesheets:
        ts_entries = ts.get("entries", [])
        for entry in ts_entries:
            entry_date = entry.get("date", "")
            if _date_in_year_month(entry_date, year, mon):
                if entry.get("travel_time_minutes", 0) > 0 or entry.get("location"):
                    # Berechne Arbeitsstunden für diesen Eintrag
                    entry_obj = TimeEntry(**entry) if isinstance(entry, dict) else entry
                    working_hours = _entry_hours(entry_obj)
                    
                    date_key = entry_date
                    if date_key not in entries_dict:
                        entries_dict[date_key] = {
                            "date": entry_date,
                            "location": entry.get("location", ""),
                            "customer_project": entry.get("customer_project", ""),
                            "travel_time_minutes": entry.get("travel_time_minutes", 0),
                            "days_count": 1,
                            "working_hours": working_hours
                        }
                    else:
                        existing = entries_dict[date_key]
                        existing["travel_time_minutes"] += entry.get("travel_time_minutes", 0)
                        existing["working_hours"] += working_hours
    
    report = TravelExpenseReport(
        user_id=current_user.id,
        user_name=current_user.name,
        month=month,
        entries=[TravelExpenseReportEntry(**e) for e in entries_dict.values()],
        status="draft"
    )
    
    report_dict = report.model_dump()
    report_dict["created_at"] = datetime.utcnow()
    report_dict["updated_at"] = datetime.utcnow()
    await db.travel_expense_reports.insert_one(report_dict)
    
    return report

@api_router.get("/travel-expense-reports/{report_id}", response_model=TravelExpenseReport)
async def get_travel_expense_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific travel expense report"""
    report = await db.travel_expense_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.can_view_all_data() and report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return TravelExpenseReport(**report)

@api_router.put("/travel-expense-reports/{report_id}", response_model=TravelExpenseReport)
async def update_travel_expense_report(
    report_id: str,
    report_update: TravelExpenseReportUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a travel expense report (only if status is draft)"""
    report = await db.travel_expense_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.can_view_all_data() and report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if report.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Can only update draft reports")
    
    update_data = report_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.travel_expense_reports.update_one(
        {"id": report_id},
        {"$set": update_data}
    )
    
    updated_report = await db.travel_expense_reports.find_one({"id": report_id})
    return TravelExpenseReport(**updated_report)

@api_router.post("/travel-expense-reports/{report_id}/submit")
async def submit_expense_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Submit expense report - sets status to 'in_review' and triggers review"""
    report = await db.travel_expense_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.can_view_all_data() and report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if report.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft reports can be submitted")
    
    # Validierung: Für alle relevanten Report-Tage muss es freigegebene, unterschriebene und verifizierte Stundenzettel geben
    try:
      entries = report.get("entries", [])
      missing_dates = []
      for e in entries:
          d = e.get("date") if isinstance(e, dict) else getattr(e, "date", None)
          if not d:
              continue
          # Suche Timesheet mit passender Woche, approved, mit verifizierter Unterschrift
          ts = await db.timesheets.find_one({
              "user_id": report["user_id"],
              "status": "approved",
              "signed_pdf_path": {"$ne": None},
              "signed_pdf_verified": True,
              # Woche enthält Datum d
              "$expr": {
                  "$and": [
                      {"$lte": ["$week_start", d]},
                      {"$gte": ["$week_end", d]}
                  ]
              }
          })
          if not ts:
              missing_dates.append(d)
      if missing_dates:
          raise HTTPException(
              status_code=400,
              detail=f"Einreichen nicht möglich. Für folgende Tage fehlt ein freigegebener, unterschriebener und verifizierter Stundenzettel: {', '.join(missing_dates)}"
          )
    except HTTPException:
      raise
    except Exception:
      # Fallback: wenn die Wochen-Grenzprüfung per $expr nicht unterstützt ist, prüfen wir einfach, ob der Monat überhaupt verifizierte TS hat
      any_verified = await db.timesheets.find_one({
          "user_id": report["user_id"],
          "status": "approved",
          "signed_pdf_path": {"$ne": None},
          "signed_pdf_verified": True
      })
      if not any_verified:
          raise HTTPException(status_code=400, detail="Einreichen nicht möglich. Es liegt kein freigegebener, unterschriebener und verifizierter Stundenzettel vor.")

    await db.travel_expense_reports.update_one(
        {"id": report_id},
        {
            "$set": {
                "status": "in_review",
                "submitted_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Trigger automatic review with agent network (async, non-blocking)
    # EU-AI-Act: Notify user about AI processing
    try:
        from agents import AgentOrchestrator
        orchestrator = AgentOrchestrator(db=db)
        # Ensure LLM is available before starting review
        await orchestrator.ensure_llm_available()
        # Run in background task
        import asyncio
        
        # EU-AI-Act Compliance: Log AI processing start
        audit_logger.log_access(
            action="ai_processing_start",
            user_id=current_user.id,
            resource_type="report",
            resource_id=report_id,
            details={
                "ai_model": os.getenv('OLLAMA_MODEL', 'llama3.2'),
                "compliance_note": "EU-AI-Act Art. 13: Automatische Prüfung mit KI-Agenten"
            }
        )
        
        asyncio.create_task(orchestrator.review_expense_report(report_id, db))
    except Exception as e:
        logger.warning(f"Could not start agent review: {e}")
    
    return {"message": "Report submitted and queued for review"}

@limiter.limit("20/hour")  # Max 20 Belege-Uploads pro Stunde
@api_router.post("/travel-expense-reports/{report_id}/upload-receipt")
async def upload_receipt(
    request: Request,
    report_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a receipt PDF - saves to local office computer only (not webserver)
    DSGVO-Compliant: Encrypted storage, audit logging, retention management
    """
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    report = await db.travel_expense_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.can_view_all_data() and report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if report.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Can only upload receipts to draft reports")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    # DSGVO: Audit logging before upload
    audit_logger.log_access(
        action="upload",
        user_id=current_user.id,
        resource_type="receipt",
        resource_id="",  # Will be set after creation
        details={"filename": file.filename, "size": len(contents)}
    )
    
    receipt_id = str(uuid.uuid4())
    # Sanitize filename for security
    safe_filename = re.sub(r'[^\w\-_\.]', '_', file.filename)
    
    # Erstelle eindeutigen Ordner pro Reisekosten-Abrechnung: User_Monat_ReportID
    user_name_safe = re.sub(r'[^\w\-_]', '_', report.get("user_name", "Unknown"))
    month = report.get("month", "unknown")
    # Ordner-Name: User_Monat_ReportID (z.B. Max_Mustermann_2025-01_abc123)
    report_folder = f"{user_name_safe}_{month}_{report_id}"
    report_folder_path = Path(LOCAL_RECEIPTS_PATH) / "reisekosten" / report_folder
    
    # Erstelle Ordner falls nicht vorhanden
    report_folder_path.mkdir(parents=True, exist_ok=True)
    
    # Speichere PDF im Ordner der Abrechnung
    filename = f"{receipt_id}_{safe_filename}"
    local_file_path = report_folder_path / filename
    
    try:
        # Save file to local storage (office computer only)
        with open(local_file_path, 'wb') as f:
            f.write(contents)
        
        # DSGVO Art. 32: Encrypt sensitive data
        data_encryption.encrypt_file(local_file_path)
        
        # Verify file is encrypted (try to decrypt - should work)
        try:
            data_encryption.decrypt_file(local_file_path)
        except Exception as e:
            logging.error(f"File encryption verification failed: {e}")
            local_file_path.unlink()  # Delete unencrypted file
            raise HTTPException(status_code=500, detail="File encryption failed")
        
    except Exception as e:
        if local_file_path.exists():
            local_file_path.unlink()  # Clean up on error
        raise HTTPException(status_code=500, detail=f"Failed to save file to local storage: {str(e)}")
    
    receipt = TravelExpenseReceipt(
        filename=file.filename,
        local_path=str(local_file_path),
        file_size=len(contents)
    )
    
    report_receipts = report.get("receipts", [])
    report_receipts.append(receipt.model_dump())
    
    await db.travel_expense_reports.update_one(
        {"id": report_id},
        {
            "$set": {
                "receipts": report_receipts,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Update audit log with receipt_id
    audit_logger.log_access(
        action="upload_complete",
        user_id=current_user.id,
        resource_type="receipt",
        resource_id=receipt.id,
        details={"local_path": str(local_file_path), "encrypted": True}
    )

    # Automatische Analyse des hochgeladenen Dokuments
    try:
        from agents import DocumentAgent, AgentOrchestrator
        from ollama_llm import OllamaLLM
        
        llm = OllamaLLM()
        document_agent = DocumentAgent(llm, db=db)
        await document_agent.initialize()
        
        # Entschlüssele Datei temporär für Analyse (wird danach wieder verschlüsselt)
        from compliance import DataEncryption
        data_encryption_temp = DataEncryption()
        try:
            data_encryption_temp.decrypt_file(local_file_path)
        except Exception as e:
            logging.warning(f"Datei konnte nicht entschlüsselt werden für Analyse: {e}")
        
        # Analysiere das Dokument
        analysis = await document_agent.analyze_document(
            str(local_file_path),
            file.filename,
            encryption=None
        )
        
        # Verschlüssele Datei wieder nach Analyse
        try:
            data_encryption_temp.encrypt_file(local_file_path)
        except Exception as e:
            logging.warning(f"Datei konnte nach Analyse nicht wieder verschlüsselt werden: {e}")
        
        # Speichere Analyse im Report
        report_document_analyses = report.get("document_analyses", [])
        report_document_analyses.append({
            "receipt_id": receipt.id,
            "analysis": analysis.model_dump()
        })
        
        # Automatische Zuordnung zu Report-Einträgen basierend auf Datum
        report_entries = report.get("entries", [])
        doc_date = analysis.extracted_data.get("date")
        
        if doc_date and report_entries:
            # Finde passenden Eintrag basierend auf Datum
            matching_entry = None
            for entry in report_entries:
                if entry.get("date") == doc_date:
                    matching_entry = entry
                    break
            
            # Wenn kein exaktes Datum-Match, suche nach ähnlichem Datum (±1 Tag)
            if not matching_entry:
                from datetime import datetime, timedelta
                try:
                    doc_date_obj = datetime.strptime(doc_date, "%Y-%m-%d")
                    for entry in report_entries:
                        entry_date_obj = datetime.strptime(entry.get("date"), "%Y-%m-%d")
                        if abs((doc_date_obj - entry_date_obj).days) <= 1:
                            matching_entry = entry
                            break
                except:
                    pass
        
        # Logik-Prüfung: Überlappende Hotelrechnungen, Datum-Abgleich mit Arbeitsstunden
        logic_issues = []
        if analysis.document_type == "hotel_receipt" and doc_date:
            # Prüfe auf überlappende Hotelrechnungen
            for existing_analysis in report_document_analyses[:-1]:  # Alle außer dem aktuellen
                existing_analysis_obj = existing_analysis.get("analysis", {})
                if existing_analysis_obj.get("document_type") == "hotel_receipt":
                    existing_date = existing_analysis_obj.get("extracted_data", {}).get("date")
                    if existing_date:
                        try:
                            from datetime import datetime
                            doc_date_obj = datetime.strptime(doc_date, "%Y-%m-%d")
                            existing_date_obj = datetime.strptime(existing_date, "%Y-%m-%d")
                            # Prüfe auf Überlappung (±3 Tage = mögliche Überlappung)
                            if abs((doc_date_obj - existing_date_obj).days) <= 3:
                                logic_issues.append(f"Mögliche überlappende Hotelrechnung: {existing_date} und {doc_date}")
                        except:
                            pass
            
            # Prüfe Datum-Abgleich mit Arbeitsstunden
            if matching_entry:
                working_hours = matching_entry.get("working_hours", 0.0)
                if working_hours == 0.0:
                    logic_issues.append(f"Für {doc_date} sind keine Arbeitsstunden im Stundenzettel verzeichnet")
            else:
                logic_issues.append(f"Kein passender Reiseeintrag für Hotelrechnung am {doc_date} gefunden")
        
        # Prüfe auf Fremdwährung - Nachweis erforderlich
        currency = analysis.extracted_data.get("currency", "EUR")
        if currency and currency.upper() != "EUR":
            # Fremdwährung erkannt - Nachweis erforderlich
            if not logic_issues:
                logic_issues = []
            logic_issues.append(f"Fremdwährung ({currency}) erkannt. Bitte laden Sie einen Nachweis über den tatsächlichen Euro-Betrag hoch (z.B. Kontoauszug).")
            # Markiere Receipt als benötigt Nachweis
            receipt_dict = receipt.model_dump()
            receipt_dict["needs_exchange_proof"] = True
            receipt_dict["currency"] = currency
            # Update Receipt im Report
            for i, r in enumerate(report_receipts):
                if r.get("id") == receipt.id:
                    report_receipts[i] = receipt_dict
                    break
        
        # Speichere Logik-Prüfung in der Analyse
        if logic_issues:
            analysis.validation_issues.extend(logic_issues)
            analysis_dict = analysis.model_dump()
            analysis_dict["logic_issues"] = logic_issues
            report_document_analyses[-1]["analysis"] = analysis_dict
        
        # Update Report mit Analysen und aktualisierten Receipts
        await db.travel_expense_reports.update_one(
            {"id": report_id},
            {
                "$set": {
                    "document_analyses": report_document_analyses,
                    "receipts": report_receipts,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Wenn Probleme gefunden, Chat-Agent benachrichtigen
        if analysis.validation_issues or logic_issues:
            try:
                from agents import ChatAgent
                chat_agent = ChatAgent(llm, db=db)
                await chat_agent.initialize()
                
                # Erstelle Chat-Nachricht für User
                issues_text = "\n".join(analysis.validation_issues + logic_issues)
                chat_message = f"Beim Hochladen von '{file.filename}' wurden folgende Punkte festgestellt:\n\n{issues_text}\n\nBitte klären Sie diese Punkte."
                
                # Speichere Chat-Nachricht
                chat_messages = report.get("chat_messages", [])
                chat_messages.append({
                    "id": str(uuid.uuid4()),
                    "sender": "agent",
                    "message": chat_message,
                    "created_at": datetime.utcnow().isoformat()
                })
                
                await db.travel_expense_reports.update_one(
                    {"id": report_id},
                    {
                        "$set": {
                            "chat_messages": chat_messages,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            except Exception as e:
                logging.warning(f"Chat-Agent Benachrichtigung fehlgeschlagen: {e}")
        
    except Exception as e:
        logging.warning(f"Automatische Dokumentenanalyse fehlgeschlagen: {e}")
        # Fehler nicht kritisch - Dokument wurde trotzdem hochgeladen
    
    # Push-Benachrichtigung an Buchhaltung: Neuer Beleg-Upload
    try:
        await notify_role(
            role="accounting",
            title="Neuer Beleg hochgeladen",
            body=f"{report.get('user_name', 'User')} hat einen Beleg für {report.get('month', '')} hochgeladen.",
            data={"type": "receipt_upload", "report_id": report_id}
        )
    except Exception as e:
        logging.warning(f"Push notify (accounting) failed: {e}")
    
    return {
        "message": "Receipt uploaded successfully and encrypted",
        "receipt_id": receipt.id,
        "analysis_completed": True,
        "has_issues": len(analysis.validation_issues) > 0 if 'analysis' in locals() else False
    }

@limiter.limit("20/hour")  # Max 20 Nachweis-Uploads pro Stunde
@api_router.post("/travel-expense-reports/{report_id}/receipts/{receipt_id}/upload-exchange-proof")
async def upload_exchange_proof(
    request: Request,
    report_id: str,
    receipt_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload exchange proof (Kontoauszug) for foreign currency receipts
    DSGVO-Compliant: Encrypted storage, audit logging
    """
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    report = await db.travel_expense_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.can_view_all_data() and report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if report.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Can only upload exchange proof to draft reports")
    
    receipts = report.get("receipts", [])
    receipt = next((r for r in receipts if r.get("id") == receipt_id), None)
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Prüfe ob Receipt Fremdwährung hat
    if not receipt.get("needs_exchange_proof") and not receipt.get("currency"):
        raise HTTPException(status_code=400, detail="This receipt does not require an exchange proof (not a foreign currency receipt)")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    # DSGVO: Audit logging
    audit_logger.log_access(
        action="upload_exchange_proof",
        user_id=current_user.id,
        resource_type="receipt",
        resource_id=receipt_id,
        details={"filename": file.filename, "size": len(contents), "receipt_id": receipt_id}
    )
    
    # Erstelle eindeutigen Ordner pro Reisekosten-Abrechnung
    user_name_safe = re.sub(r'[^\w\-_]', '_', report.get("user_name", "Unknown"))
    month = report.get("month", "unknown")
    report_folder = f"{user_name_safe}_{month}_{report_id}"
    report_folder_path = Path(LOCAL_RECEIPTS_PATH) / "reisekosten" / report_folder
    
    # Erstelle Ordner falls nicht vorhanden
    report_folder_path.mkdir(parents=True, exist_ok=True)
    
    # Speichere PDF im Ordner der Abrechnung
    safe_filename = re.sub(r'[^\w\-_\.]', '_', file.filename)
    proof_filename = f"exchange_proof_{receipt_id}_{safe_filename}"
    local_file_path = report_folder_path / proof_filename
    
    try:
        # Save file to local storage
        with open(local_file_path, 'wb') as f:
            f.write(contents)
        
        # DSGVO Art. 32: Encrypt sensitive data
        data_encryption.encrypt_file(local_file_path)
        
        # Verify file is encrypted
        try:
            data_encryption.decrypt_file(local_file_path)
        except Exception as e:
            logging.error(f"File encryption verification failed: {e}")
            local_file_path.unlink()
            raise HTTPException(status_code=500, detail="File encryption failed")
        
    except Exception as e:
        if local_file_path.exists():
            local_file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Update Receipt mit Nachweis
    receipt["exchange_proof_path"] = str(local_file_path)
    receipt["exchange_proof_filename"] = file.filename
    
    # Update Report
    await db.travel_expense_reports.update_one(
        {"id": report_id},
        {
            "$set": {
                "receipts": receipts,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Update audit log
    audit_logger.log_access(
        action="upload_exchange_proof_complete",
        user_id=current_user.id,
        resource_type="receipt",
        resource_id=receipt_id,
        details={"local_path": str(local_file_path), "encrypted": True}
    )
    
    return {
        "message": "Exchange proof uploaded successfully and encrypted",
        "receipt_id": receipt_id
    }

@api_router.delete("/travel-expense-reports/{report_id}/receipts/{receipt_id}")
async def delete_receipt(
    report_id: str,
    receipt_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a receipt from a report"""
    report = await db.travel_expense_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.can_view_all_data() and report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if report.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Can only delete receipts from draft reports")
    
    receipts = report.get("receipts", [])
    receipt_to_delete = next((r for r in receipts if r.get("id") == receipt_id), None)
    
    if not receipt_to_delete:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    try:
        local_path = Path(receipt_to_delete.get("local_path", ""))
        if local_path.exists():
            local_path.unlink()
        # Lösche auch den Fremdwährungs-Nachweis falls vorhanden
        exchange_proof_path = receipt_to_delete.get("exchange_proof_path")
        if exchange_proof_path:
            proof_path = Path(exchange_proof_path)
            if proof_path.exists():
                proof_path.unlink()
    except Exception as e:
        logging.warning(f"Failed to delete local file: {e}")
    
    receipts = [r for r in receipts if r.get("id") != receipt_id]
    await db.travel_expense_reports.update_one(
        {"id": report_id},
        {
            "$set": {
                "receipts": receipts,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Receipt deleted successfully"}

@api_router.delete("/travel-expense-reports/{report_id}")
async def delete_expense_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an expense report (only if draft)"""
    report = await db.travel_expense_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.can_view_all_data() and report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if report.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Can only delete draft reports")
    
    # Lösche alle Belege und den gesamten Ordner der Abrechnung
    receipts = report.get("receipts", [])
    for receipt in receipts:
        try:
            local_path = Path(receipt.get("local_path", ""))
            if local_path.exists():
                local_path.unlink()
        except Exception as e:
            logging.warning(f"Failed to delete local file: {e}")
    
    # Lösche den gesamten Ordner der Abrechnung (falls leer oder mit Belegen)
    try:
        user_name_safe = re.sub(r'[^\w\-_]', '_', report.get("user_name", "Unknown"))
        month = report.get("month", "unknown")
        report_folder = f"{user_name_safe}_{month}_{report_id}"
        report_folder_path = Path(LOCAL_RECEIPTS_PATH) / "reisekosten" / report_folder
        
        # Lösche Ordner und alle Inhalte
        if report_folder_path.exists():
            import shutil
            shutil.rmtree(report_folder_path)
            logging.info(f"Deleted report folder: {report_folder_path}")
    except Exception as e:
        logging.warning(f"Failed to delete report folder: {e}")
    
    await db.travel_expense_reports.delete_one({"id": report_id})
    return {"message": "Report deleted successfully"}

@api_router.get("/travel-expense-reports/{report_id}/chat", response_model=List[ChatMessage])
async def get_chat_messages(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get chat messages for a report"""
    report = await db.travel_expense_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.can_view_all_data() and report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    messages = []
    async for msg in db.chat_messages.find({"report_id": report_id}).sort("created_at", 1):
        messages.append(ChatMessage(**msg))
    
    return messages

@api_router.post("/travel-expense-reports/{report_id}/chat")
async def send_chat_message(
    report_id: str,
    message: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Send a chat message (user or agent)"""
    report = await db.travel_expense_reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not current_user.can_view_all_data() and report["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    user_msg = ChatMessage(
        report_id=report_id,
        sender="user",
        message=message
    )
    
    user_msg_dict = user_msg.model_dump()
    user_msg_dict["created_at"] = datetime.utcnow()
    await db.chat_messages.insert_one(user_msg_dict)
    
    # If report is in_review, trigger agent response
    if report.get("status") == "in_review":
        try:
            from agents import AgentOrchestrator
            orchestrator = AgentOrchestrator(db=db)
            # Ensure LLM is available
            await orchestrator.ensure_llm_available()
            agent_response = await orchestrator.handle_user_message(report_id, message, db)
            
            # If agent needs more info or wants to continue, it will be handled by the response
            return agent_response.model_dump()
        except Exception as e:
            logger.warning(f"Could not get agent response: {e}")
    
    return user_msg

# ============================================================================
# Urlaubsplaner Endpunkte
# ============================================================================

@api_router.get("/vacation/requests", response_model=List[VacationRequest])
async def get_vacation_requests(
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get vacation requests for current user, or all if admin/accounting"""
    query = {}
    if not current_user.can_view_all_data():
        query["user_id"] = current_user.id
    
    if year:
        query["year"] = year
    
    requests = []
    async for req in db.vacation_requests.find(query).sort("created_at", -1):
        requests.append(VacationRequest(**req))
    return requests

@api_router.post("/vacation/requests", response_model=VacationRequest)
async def create_vacation_request(
    request_create: VacationRequestCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new vacation request"""
    from datetime import date
    start = datetime.strptime(request_create.start_date, "%Y-%m-%d")
    end = datetime.strptime(request_create.end_date, "%Y-%m-%d")
    
    if start > end:
        raise HTTPException(status_code=400, detail="Startdatum muss vor Enddatum liegen")
    
    year = start.year
    working_days = count_working_days(request_create.start_date, request_create.end_date)
    
    if working_days <= 0:
        raise HTTPException(status_code=400, detail="Keine Werktage im angegebenen Zeitraum")
    
    # Prüfe Urlaubsguthaben
    balance = await db.vacation_balances.find_one({
        "user_id": current_user.id,
        "year": year
    })
    
    if balance:
        used_days = balance.get("used_days", 0)
        total_days = balance.get("total_days", 0)
        
        # Berechne bereits genehmigte Tage für dieses Jahr
        approved_requests = await db.vacation_requests.find({
            "user_id": current_user.id,
            "year": year,
            "status": "approved"
        }).to_list(100)
        approved_days = sum(r.get("working_days", 0) for r in approved_requests)
        
        if approved_days + working_days > total_days:
            raise HTTPException(
                status_code=400,
                detail=f"Nicht genug Urlaubstage verfügbar. Verfügbar: {total_days - approved_days}, benötigt: {working_days}"
            )
    
    request = VacationRequest(
        user_id=current_user.id,
        user_name=current_user.name,
        start_date=request_create.start_date,
        end_date=request_create.end_date,
        working_days=working_days,
        year=year,
        notes=request_create.notes
    )
    
    request_dict = request.model_dump()
    request_dict["created_at"] = datetime.utcnow()
    await db.vacation_requests.insert_one(request_dict)
    
    return request

@api_router.delete("/vacation/requests/{request_id}")
async def delete_vacation_request(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a vacation request (only if pending and own request, or admin/accounting)"""
    request = await db.vacation_requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Urlaubsantrag nicht gefunden")
    
    # Nur eigene pending Anträge können gelöscht werden, oder Admin/Buchhaltung
    if request["status"] == "approved" and not current_user.can_view_all_data():
        raise HTTPException(status_code=400, detail="Genehmigte Anträge können nicht gelöscht werden")
    
    if request["user_id"] != current_user.id and not current_user.can_view_all_data():
        raise HTTPException(status_code=403, detail="Nicht autorisiert")
    
    await db.vacation_requests.delete_one({"id": request_id})
    return {"message": "Urlaubsantrag gelöscht"}

@api_router.post("/vacation/requests/{request_id}/approve")
async def approve_vacation_request(
    request_id: str,
    current_user: User = Depends(get_accounting_or_admin_user)
):
    """Approve a vacation request (accounting/admin only)"""
    request = await db.vacation_requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Urlaubsantrag nicht gefunden")
    
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Nur ausstehende Anträge können genehmigt werden")
    
    # Update status
    await db.vacation_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": "approved",
                "reviewed_at": datetime.utcnow(),
                "reviewed_by": current_user.id
            }
        }
    )
    
    # Update vacation balance
    balance = await db.vacation_balances.find_one({
        "user_id": request["user_id"],
        "year": request["year"]
    })
    
    if balance:
        new_used = balance.get("used_days", 0) + request["working_days"]
        await db.vacation_balances.update_one(
            {"id": balance["id"]},
            {
                "$set": {
                    "used_days": new_used,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    # Push-Benachrichtigung an den User
    try:
        await notify_user(
            user_id=request["user_id"],
            title="Urlaub genehmigt",
            body=f"{request.get('user_name', 'Ihr')} Urlaub {request.get('start_date', '')} bis {request.get('end_date', '')} wurde genehmigt.",
            data={"type": "vacation_approved", "request_id": request_id}
        )
    except Exception as e:
        logging.warning(f"Push notify (vacation approved) failed: {e}")

    return {"message": "Urlaubsantrag genehmigt"}

@api_router.post("/vacation/requests/{request_id}/reject")
async def reject_vacation_request(
    request_id: str,
    current_user: User = Depends(get_accounting_or_admin_user)
):
    """Reject a vacation request (accounting/admin only)"""
    request = await db.vacation_requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Urlaubsantrag nicht gefunden")
    
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Nur ausstehende Anträge können abgelehnt werden")
    
    await db.vacation_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": "rejected",
                "reviewed_at": datetime.utcnow(),
                "reviewed_by": current_user.id
            }
        }
    )
    
    return {"message": "Urlaubsantrag abgelehnt"}

@api_router.get("/vacation/balance", response_model=List[VacationBalance])
async def get_vacation_balance(
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get vacation balance for current user, or all if admin/accounting"""
    query = {}
    if not current_user.can_view_all_data():
        query["user_id"] = current_user.id
    
    if year:
        query["year"] = year
    
    balances = []
    async for bal in db.vacation_balances.find(query).sort("year", -1):
        balances.append(VacationBalance(**bal))
    return balances

@api_router.put("/vacation/balance/{user_id}/{year}", response_model=VacationBalance)
async def update_vacation_balance(
    user_id: str,
    year: int,
    balance_update: VacationBalanceUpdate,
    current_user: User = Depends(get_admin_user)
):
    """Update vacation balance (admin only)"""
    balance = await db.vacation_balances.find_one({"user_id": user_id, "year": year})
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    
    if balance:
        # Update existing
        await db.vacation_balances.update_one(
            {"id": balance["id"]},
            {
                "$set": {
                    "total_days": balance_update.total_days,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        updated = await db.vacation_balances.find_one({"id": balance["id"]})
        return VacationBalance(**updated)
    else:
        # Create new
        new_balance = VacationBalance(
            user_id=user_id,
            user_name=user.get("name", ""),
            year=year,
            total_days=balance_update.total_days,
            used_days=0
        )
        balance_dict = new_balance.model_dump()
        balance_dict["created_at"] = datetime.utcnow()
        balance_dict["updated_at"] = datetime.utcnow()
        await db.vacation_balances.insert_one(balance_dict)
        return new_balance

@api_router.delete("/vacation/requests/{request_id}/admin-delete")
async def admin_delete_vacation_request(
    request_id: str,
    current_user: User = Depends(get_admin_user)
):
    """Delete approved vacation request (admin only) - updates balance"""
    request = await db.vacation_requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Urlaubsantrag nicht gefunden")
    
    # Wenn approved, reduziere used_days im Balance
    if request["status"] == "approved":
        balance = await db.vacation_balances.find_one({
            "user_id": request["user_id"],
            "year": request["year"]
        })
        if balance:
            new_used = max(0, balance.get("used_days", 0) - request["working_days"])
            await db.vacation_balances.update_one(
                {"id": balance["id"]},
                {
                    "$set": {
                        "used_days": new_used,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
    
    await db.vacation_requests.delete_one({"id": request_id})
    return {"message": "Urlaubsantrag gelöscht"}

@api_router.get("/vacation/requirements/{year}")
async def get_vacation_requirements(
    year: int,
    current_user: User = Depends(get_current_user)
):
    """Check vacation requirements for current user"""
    return await check_vacation_requirements(year, current_user.id, db)

@api_router.get("/vacation/holidays/{year}")
async def get_holidays(year: int):
    """Get German and Saxon holidays for a year (programmweit verfügbar)"""
    holidays_set = get_german_holidays(year)
    # Sortiere und formatiere als Liste von Datumsstrings
    holidays_list = sorted([date.strftime("%Y-%m-%d") for date in holidays_set])
    return {
        "year": year,
        "holidays": holidays_list,
        "count": len(holidays_list)
    }

@api_router.get("/vacation/check-holiday/{date}")
async def check_holiday(date: str):
    """Check if a specific date is a holiday (German or Saxon)"""
    return {
        "date": date,
        "is_holiday": is_holiday(date)
    }

@api_router.post("/vacation/send-reminders")
async def send_vacation_reminders(current_user: User = Depends(get_admin_user)):
    """Send weekly reminder emails to users who haven't met vacation requirements (admin only)"""
    from datetime import date
    current_year = date.today().year
    deadline = date(current_year, 2, 1)
    today = date.today()
    
    # Only send reminders after deadline has passed or approaching
    if today > deadline:
        return {"message": f"Deadline ({deadline}) bereits verstrichen. Keine Erinnerungen mehr nötig."}
    
    # Get all users
    all_users = await db.users.find({"role": {"$ne": "admin"}}).to_list(1000)
    
    # Get SMTP config
    smtp_config = await db.smtp_config.find_one()
    if not smtp_config:
        raise HTTPException(status_code=400, detail="SMTP-Konfiguration nicht gefunden")
    
    reminders_sent = 0
    errors = []
    
    for user in all_users:
        try:
            requirements = await check_vacation_requirements(current_year, user["id"], db)
            
            if requirements["needs_reminder"]:
                # Send reminder email
                msg = MIMEMultipart()
                msg['From'] = smtp_config["smtp_username"]
                msg['To'] = user["email"]
                msg['Subject'] = f"Erinnerung: Urlaubsplanung für {current_year}"
                
                body = f"""Hallo {user.get('name', '')},

diese E-Mail erinnert Sie daran, Ihre Urlaubsplanung für das Jahr {current_year} zu vervollständigen.

**Aktueller Status:**
- Mindestens 2 Wochen am Stück (gesetzlicher Erholungsurlaub - BUrlG §7): {'✓' if requirements['meets_min_consecutive'] else '✗'} (aktuell: {requirements['max_consecutive']} Tage)
- Insgesamt mindestens 20 Tage geplant (betriebliche Vorgabe): {'✓' if requirements['meets_min_total'] else '✗'} (aktuell: {requirements['total_days']} Tage)
- Geplant bis 01.02.{current_year} (betriebliche Vorgabe): {'✓' if requirements['meets_deadline'] else '✗'}

**Bitte planen Sie Ihre Urlaubstage bis zum 01.02.{current_year} ein.**

Sie können Ihre Urlaubsanträge im System unter "Urlaubsplaner" stellen.

Mit freundlichen Grüßen
{COMPANY_INFO["name"]}
                """
                
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                server = smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"])
                server.starttls()
                server.login(smtp_config["smtp_username"], smtp_config["smtp_password"])
                server.sendmail(smtp_config["smtp_username"], [user["email"]], msg.as_string().encode('utf-8'))
                server.quit()
                
                reminders_sent += 1
                logger.info(f"Urlaubserinnerung gesendet an {user['email']}")
                
        except Exception as e:
            errors.append(f"Fehler bei {user.get('email', 'unbekannt')}: {str(e)}")
            logger.error(f"Fehler beim Senden der Urlaubserinnerung: {e}")
    
    return {
        "message": f"Erinnerungsmails versendet",
        "reminders_sent": reminders_sent,
        "errors": errors if errors else None
    }

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()