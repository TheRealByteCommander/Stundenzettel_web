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
    is_admin: bool = False
    hashed_password: str
    two_fa_enabled: bool = False
    two_fa_secret: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    is_admin: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    otp: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    is_admin: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class TwoFAVerify(BaseModel):
    otp: str
    temp_token: str

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

class TimeEntry(BaseModel):
    date: str  # YYYY-MM-DD format
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    break_minutes: int
    tasks: str
    customer_project: str
    location: str

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
    status: str = "draft"  # draft, sent

class WeeklyTimesheetCreate(BaseModel):
    week_start: str
    entries: List[TimeEntry]

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
    if not entry.start_time or not entry.end_time:
        return 0.0
    try:
        sh, sm = map(int, entry.start_time.split(":"))
        eh, em = map(int, entry.end_time.split(":"))
        start = sh * 60 + sm
        end = eh * 60 + em
        worked = max(0, end - start - int(entry.break_minutes))
        return max(0.0, worked / 60.0)
    except Exception:
        return 0.0

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
        return User(**user)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
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
            
            # Only show times if they are entered
            if entry.start_time and entry.end_time:
                row[1] = entry.start_time  # Startzeit
                row[2] = entry.end_time    # Endzeit
                row[3] = f"{entry.break_minutes} Min"  # Pause
                
                # Calculate daily hours
                start_parts = entry.start_time.split(':')
                end_parts = entry.end_time.split(':')
                start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
                end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
                worked_minutes = end_minutes - start_minutes - entry.break_minutes
                daily_hours = worked_minutes / 60
                total_hours += daily_hours
                row[5] = f"{daily_hours:.1f}h"  # Arbeitszeit
            
            # Always show description if available
            row[4] = entry.tasks if entry.tasks else ""  # Beschreibung
        
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

# Routes
@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "is_admin": current_user.is_admin
    }

@api_router.post("/auth/login")
async def login(user_login: UserLogin):
    user = await db.users.find_one({"email": user_login.email})
    if not user or not verify_password(user_login.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # 2FA flow
    if user.get("two_fa_enabled") and user.get("two_fa_secret"):
        # If OTP provided directly, verify it, else return challenge
        if not user_login.otp:
            temp_token = create_access_token(
                data={"sub": user["email"], "scope": "2fa"}, expires_delta=timedelta(minutes=5)
            )
            return {"requires_2fa": True, "temp_token": temp_token}
        # Verify provided OTP
        totp = pyotp.TOTP(user["two_fa_secret"])
        if not totp.verify(user_login.otp, valid_window=1):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

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

@api_router.post("/auth/register")
async def register(user_create: UserCreate, current_user: User = Depends(get_admin_user)):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_create.password)
    user = User(
        email=user_create.email,
        name=user_create.name,
        is_admin=user_create.is_admin,
        hashed_password=hashed_password
    )
    
    await db.users.insert_one(user.model_dump())
    return {"message": "User created successfully", "user_id": user.id}

@api_router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(current_user: User = Depends(get_admin_user)):
    users = await db.users.find().to_list(1000)
    return [{"id": user["id"], "email": user["email"], "name": user["name"], "is_admin": user["is_admin"]} for user in users]

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
    
    if user_update.is_admin is not None:
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
    if user["is_admin"]:
        # Count total number of admin users
        admin_count = await db.users.count_documents({"is_admin": True})
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
    # Generate secret and store temporarily for the user
    secret = pyotp.random_base32()
    await db.users.update_one({"id": current_user.id}, {"$set": {"two_fa_secret": secret}})
    issuer = COMPANY_INFO["name"]
    otpauth_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name=issuer)
    return {"secret": secret, "otpauth_uri": otpauth_uri}

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
async def disable_two_fa(current_user: User = Depends(get_current_user)):
    await db.users.update_one({"id": current_user.id}, {"$set": {"two_fa_enabled": False, "two_fa_secret": None}})
    return {"message": "2FA disabled"}

# Stats: total sent hours per user per month (YYYY-MM)
@api_router.get("/stats/monthly", response_model=MonthlyStatsResponse)
async def get_monthly_stats(month: str, current_user: User = Depends(get_current_user)):
    # Validate month format
    try:
        year, mon = map(int, month.split("-"))
        _ = datetime(year, mon, 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    # Query only sent timesheets
    query = {"status": "sent"}
    if not current_user.is_admin:
        query["user_id"] = current_user.id

    ts = await db.timesheets.find(query).to_list(5000)

    # Aggregate hours per user for the given month, counting only entries within that month
    user_totals: Dict[str, Dict[str, Any]] = {}
    for t in ts:
        user_id = t.get("user_id")
        user_name = t.get("user_name", "")
        entries = t.get("entries", [])
        monthly_hours = 0.0
        for e in entries:
            try:
                # Works with dict entries or already validated
                e_date = e.get("date") if isinstance(e, dict) else e.date
                if _date_in_year_month(e_date, year, mon):
                    entry_obj = e if isinstance(e, dict) else e.model_dump()
                    te = TimeEntry(**entry_obj)
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

    # For non-admins, ensure at least their user appears with 0 if none found
    if not current_user.is_admin and not stats:
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

    # All sent timesheets
    ts = await db.timesheets.find({"status": "sent"}).to_list(5000)

    # Aggregate totals per user
    totals: Dict[str, float] = {}
    names: Dict[str, str] = {}
    for t in ts:
        uid = t.get("user_id")
        names[uid] = t.get("user_name", names.get(uid, ""))
        entries = t.get("entries", [])
        hours = 0.0
        for e in entries:
            try:
                e_date = e.get("date") if isinstance(e, dict) else e.date
                if _date_in_year_month(e_date, year, mon):
                    entry_obj = e if isinstance(e, dict) else e.model_dump()
                    te = TimeEntry(**entry_obj)
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
    if current_user.is_admin:
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
    
    # Check permissions (admin can edit any, user can edit their own)
    if not current_user.is_admin and timesheet["user_id"] != current_user.id:
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
    
    # Check permissions (admin can delete any, user can delete their own)
    if not current_user.is_admin and timesheet["user_id"] != current_user.id:
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

# Initialize admin user on startup
@app.on_event("startup")
async def create_admin_user():
    admin = await db.users.find_one({"email": "admin@schmitz-intralogistik.de"})
    if not admin:
        admin_user = User(
            email="admin@schmitz-intralogistik.de",
            name="Administrator",
            is_admin=True,
            hashed_password=get_password_hash("admin123")
        )
        await db.users.insert_one(admin_user.dict())
        print("Admin user created: admin@schmitz-intralogistik.de / admin123")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()