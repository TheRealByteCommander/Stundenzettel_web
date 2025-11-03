from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Form, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

# JWT and Password settings
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(title="Schmitz Intralogistik Zeiterfassung")
api_router = APIRouter(prefix="/api")

# Company Information
COMPANY_INFO = {
    "name": "Schmitz Intralogistik GmbH",
    "address": "Grüner Weg 3",
    "city": "04827 Machern",
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

class TimesheetUpdate(BaseModel):
    week_start: Optional[str] = None
    entries: Optional[List[TimeEntry]] = None

class WeeklyTimesheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    week_start: str  # Monday date in YYYY-MM-DD format
    week_end: str    # Sunday date in YYYY-MM-DD format
    entries: List[TimeEntry]
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

class TravelExpenseReportEntry(BaseModel):
    date: str  # YYYY-MM-DD
    location: str  # Ort aus Stundenzettel
    customer_project: str  # Kunde/Projekt
    travel_time_minutes: int  # Fahrzeit
    days_count: int = 1  # Anzahl Tage

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

def _entry_hours(entry: TimeEntry) -> float:
    """Calculate working hours including travel time if include_travel_time is True"""
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
    
    # Add travel time if checkbox is checked (always add to DB working hours)
    # Note: This is always counted in DB for statistics, but only shown on PDF if include_travel_time is True
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
    
    company_info = f"""<b>Schmitz Intralogistik GmbH</b><br/>
    Grüner Weg 3<br/>
    04827 Machern, Deutschland"""
    
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
                if entry.include_travel_time and entry.travel_time_minutes and entry.travel_time_minutes > 0:
                    daily_hours += entry.travel_time_minutes / 60.0
                    # Add travel time info to description
                    travel_hours = entry.travel_time_minutes / 60.0
                    if entry.tasks:
                        row[4] = f"{entry.tasks} (Fahrzeit: {travel_hours:.1f}h)"
                    else:
                        row[4] = f"Fahrzeit: {travel_hours:.1f}h"
                else:
                    # Regular description without travel time
                    row[4] = entry.tasks if entry.tasks else ""
                
                # Note: Travel time is ALWAYS counted in DB (_entry_hours), but only shown on PDF if include_travel_time=True
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
    
    company_info = f"""<b>Schmitz Intralogistik GmbH</b><br/>
    Grüner Weg 3<br/>
    04827 Machern, Deutschland"""
    
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

@api_router.post("/auth/login")
async def login(user_login: UserLogin):
    user = await db.users.find_one({"email": user_login.email})
    if not user or not verify_password(user_login.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # 2FA is mandatory - check if user has 2FA setup
    if not user.get("two_fa_secret"):
        # User needs to setup 2FA first
        # Generate a temporary token for 2FA setup (valid for 10 minutes)
        setup_token = create_access_token(
            data={"sub": user["email"], "scope": "2fa_setup"}, expires_delta=timedelta(minutes=10)
        )
        return {"requires_2fa_setup": True, "setup_token": setup_token}
    
    # 2FA is mandatory - user must provide OTP
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

@api_router.post("/auth/register")
async def register(user_create: UserCreate, current_user: User = Depends(get_admin_user)):
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
    """Approve a timesheet - only accounting or admin can approve"""
    # Find timesheet
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Only sent timesheets can be approved
    if timesheet["status"] not in ["sent", "draft"]:
        raise HTTPException(status_code=400, detail="Only sent or draft timesheets can be approved")
    
    # Require uploaded, signed PDF before approval
    if not timesheet.get("signed_pdf_path"):
        raise HTTPException(
            status_code=400,
            detail="Approval requires uploaded signed timesheet PDF. Please upload the customer-signed document first."
        )
    
    # Update status to approved
    await db.timesheets.update_one(
        {"id": timesheet_id},
        {"$set": {"status": "approved"}}
    )
    
    return {"message": "Timesheet approved successfully"}

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
    current_user: User = Depends(get_accounting_or_admin_user)
):
    """Generate PDF report for accounting monthly statistics"""
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
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@api_router.post("/timesheets", response_model=WeeklyTimesheet)
async def create_timesheet(timesheet_create: WeeklyTimesheetCreate, current_user: User = Depends(get_current_user)):
    # Calculate week end (Sunday)
    from datetime import datetime, timedelta
    week_start = datetime.strptime(timesheet_create.week_start, "%Y-%m-%d")
    week_end = week_start + timedelta(days=6)
    
    # Filter out entries without work times (optional - allow empty entries for flexibility)
    # valid_entries = [entry for entry in timesheet_create.entries if entry.start_time and entry.end_time]
    # Or keep all entries as they might have tasks/notes even without times
    
    timesheet = WeeklyTimesheet(
        user_id=current_user.id,
        user_name=current_user.name,
        week_start=timesheet_create.week_start,
        week_end=week_end.strftime("%Y-%m-%d"),
        entries=timesheet_create.entries  # Keep all entries, let PDF handle empty times
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

@api_router.put("/timesheets/{timesheet_id}")
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
    
    if timesheet_update.entries is not None:
        update_data["entries"] = [entry.model_dump() for entry in timesheet_update.entries]
    
    if update_data:
        await db.timesheets.update_one({"id": timesheet_id}, {"$set": update_data})
    
    return {"message": "Timesheet updated successfully"}

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
async def get_timesheet_pdf(timesheet_id: str, current_user: User = Depends(get_current_user)):
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
    
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@api_router.post("/timesheets/{timesheet_id}/download-and-email")
async def download_and_email_timesheet(timesheet_id: str, current_user: User = Depends(get_current_user)):
    """Download PDF and automatically send copy to admin"""
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
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
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

@api_router.post("/timesheets/{timesheet_id}/upload-signed")
async def upload_signed_timesheet(
    timesheet_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload unterschriebener Stundenzettel-PDF. Benachrichtigt alle Buchhaltungs-User per E-Mail."""
    
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
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timesheet_id}_signed_{timestamp}_{safe_filename}"
    local_file_path = Path(LOCAL_RECEIPTS_PATH) / "signed_timesheets" / filename
    
    # Ensure directory exists
    local_file_path.parent.mkdir(parents=True, exist_ok=True)
    
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
                    notes = "Schlüsselwörter für Unterschrift im PDF-Text gefunden."
                else:
                    notes = "Keine offensichtlichen Unterschrifts-Schlüsselwörter im PDF-Text gefunden. Manuelle Prüfung empfohlen."
            else:
                notes = "Kein Text extrahiert. Manuelle Prüfung empfohlen."
        except Exception as e:
            verified = False
            notes = f"Automatische Verifikation fehlgeschlagen: {str(e)}"

        # Update timesheet with signed PDF metadata
        await db.timesheets.update_one(
            {"id": timesheet_id},
            {
                "$set": {
                    "signed_pdf_path": str(local_file_path),
                    "signed_pdf_verified": bool(verified),
                    "signed_pdf_verification_notes": notes,
                    "status": "sent"  # Mark as sent when signed version is uploaded
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
                msg['From'] = smtp_config["smtp_username"]
                msg['Subject'] = f"Unterschriebener Stundenzettel hochgeladen - {timesheet_obj.user_name} - {week_info}"
                
                body = f"""Hallo,

ein unterschriebener Stundenzettel wurde hochgeladen:

Mitarbeiter: {timesheet_obj.user_name}
Woche: {week_info}
Stundenzettel-ID: {timesheet_id}

Der unterschriebene Stundenzettel wurde verschlüsselt im lokalen Speicher gespeichert.

Bitte prüfen Sie den Stundenzettel im System.

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
    logger.info("DSGVO Compliance: Retention manager initialized")
    logger.info("EU-AI-Act Compliance: AI transparency logging enabled")

async def create_admin_user():
    admin = await db.users.find_one({"email": "admin@schmitz-intralogistik.de"})
    if not admin:
        # Generate 2FA secret for admin (2FA is mandatory)
        two_fa_secret = pyotp.random_base32()
        admin_user = User(
            email="admin@schmitz-intralogistik.de",
            name="Administrator",
            role="admin",
            hashed_password=get_password_hash("admin123"),
            two_fa_secret=two_fa_secret,
            two_fa_enabled=False  # Will be enabled after first login with 2FA setup
        )
        admin_dict = admin_user.model_dump()
        admin_dict["is_admin"] = True  # Backward compatibility
        await db.users.insert_one(admin_dict)
        print("Admin user created: admin@schmitz-intralogistik.de / admin123")
        print("NOTE: Admin must setup 2FA on first login (2FA is mandatory)")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=[
        "https://stundenzettel.byte-commander.de",
        "http://localhost:3000",
        "http://localhost:8000"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
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
                    date_key = entry_date
                    if date_key not in entries_dict:
                        entries_dict[date_key] = {
                            "date": entry_date,
                            "location": entry.get("location", ""),
                            "customer_project": entry.get("customer_project", ""),
                            "travel_time_minutes": entry.get("travel_time_minutes", 0),
                            "days_count": 1
                        }
                    else:
                        existing = entries_dict[date_key]
                        existing["travel_time_minutes"] += entry.get("travel_time_minutes", 0)
    
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

@api_router.post("/travel-expense-reports/{report_id}/upload-receipt")
async def upload_receipt(
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
    filename = f"{report_id}_{receipt_id}_{safe_filename}"
    local_file_path = Path(LOCAL_RECEIPTS_PATH) / filename
    
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
    
    return {"message": "Receipt uploaded successfully and encrypted", "receipt_id": receipt.id}

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
    
    receipts = report.get("receipts", [])
    for receipt in receipts:
        try:
            local_path = Path(receipt.get("local_path", ""))
            if local_path.exists():
                local_path.unlink()
        except Exception as e:
            logging.warning(f"Failed to delete local file: {e}")
    
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()