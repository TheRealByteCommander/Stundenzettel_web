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
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT and Password settings
SECRET_KEY = "schmitz-intralogistik-secret-key-2025"
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
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    is_admin: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    is_admin: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

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
        return User(**user)
    except jwt.PyJWTError:
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
    
    # Create a main table that contains everything to keep it on one page
    main_table_data = []
    
    # Row 1: Company header (right aligned) and title
    company_info = f"""<b>Schmitz Intralogistik GmbH</b><br/>
    Grüner Weg 3<br/>
    04827 Machern, Deutschland<br/>
    Tel: +49 (0) 29242 9600<br/>
    www.schmitz-intralogistik.com"""
    
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    styles = getSampleStyleSheet()
    
    company_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=8,
        textColor=dark_gray,
        alignment=2,  # Right align
    )
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=dark_gray,
        alignment=1,  # Center
    )
    
    # Row 1: Header row with company info and title
    header_row = [
        Paragraph("", styles['Normal']),  # Empty left cell
        Paragraph("<b>STUNDENZETTEL</b>", title_style),
        Paragraph(company_info, company_style)
    ]
    main_table_data.append(header_row)
    
    # Row 2: Employee info
    employee_info = f"<b>Mitarbeiter:</b> {timesheet.user_name}<br/><b>Kalenderwoche:</b> {get_calendar_week(timesheet.week_start)}<br/><b>Zeitraum:</b> {timesheet.week_start} bis {timesheet.week_end}"
    employee_row = [
        Paragraph(employee_info, styles['Normal']),
        Paragraph("", styles['Normal']),  # Empty middle
        Paragraph("", styles['Normal'])   # Empty right
    ]
    main_table_data.append(employee_row)
    
    # Row 3: Weekly timesheet table
    if timesheet.entries:
        # Calculate total hours first
        total_hours = 0
        
        # Create compact weekly table
        weekly_headers = ["", "Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        dates_row = ["Datum"]
        start_row = ["Beginn"]
        end_row = ["Ende"] 
        pause_row = ["Pause"]
        tasks_row = ["Tätigkeit"]
        hours_row = ["Std."]
        
        # Fill data for each day
        entries_by_date = {entry.date: entry for entry in timesheet.entries}
        
        # Get week dates
        from datetime import datetime, timedelta
        week_start_date = datetime.strptime(timesheet.week_start, "%Y-%m-%d")
        
        for i in range(7):  # Monday to Sunday
            current_date = week_start_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            display_date = current_date.strftime("%d.%m")
            
            dates_row.append(display_date)
            
            if date_str in entries_by_date:
                entry = entries_by_date[date_str]
                start_row.append(entry.start_time)
                end_row.append(entry.end_time)
                pause_row.append(f"{entry.break_minutes}'")
                # Truncate long task descriptions
                task_short = entry.tasks[:12] + "..." if len(entry.tasks) > 12 else entry.tasks
                tasks_row.append(task_short)
                
                # Calculate daily hours
                start_parts = entry.start_time.split(':')
                end_parts = entry.end_time.split(':')
                start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
                end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
                worked_minutes = end_minutes - start_minutes - entry.break_minutes
                daily_hours = worked_minutes / 60
                total_hours += daily_hours
                hours_row.append(f"{daily_hours:.1f}")
            else:
                start_row.append("")
                end_row.append("")
                pause_row.append("")
                tasks_row.append("")
                hours_row.append("")
        
        # Build compact weekly table
        weekly_data = [
            weekly_headers,
            dates_row,
            start_row,
            end_row,
            pause_row,
            tasks_row,
            hours_row
        ]
        
        # Create table with smaller columns
        col_width = (page_width - 80) / 8  # 8 columns
        weekly_table = Table(weekly_data, colWidths=[80] + [col_width] * 7)
        
        # Compact table styling
        weekly_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), company_red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            
            # Label column
            ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            
            # All cells
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, dark_gray),
            
            # Minimal padding
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        # Add weekly table as single cell spanning all columns
        weekly_row = [weekly_table, "", ""]
        main_table_data.append(weekly_row)
        
        # Row 4: Total hours and signatures in one row
        total_and_sig = f"""<b>GESAMTSTUNDEN: {total_hours:.2f}</b><br/>
        Erstellt: {timesheet.created_at.strftime("%d.%m.%Y")}<br/><br/>
        Unterschrift Mitarbeiter: _________________________<br/><br/>
        Unterschrift Auftraggeber: _______________________"""
        
        signature_style = ParagraphStyle(
            'Signature',
            parent=styles['Normal'],
            fontSize=9,
            textColor=dark_gray,
        )
        
        final_row = [
            Paragraph(total_and_sig, signature_style),
            Paragraph("", styles['Normal']),
            Paragraph("", styles['Normal'])
        ]
        main_table_data.append(final_row)
    
    # Create main table that keeps everything on one page
    main_table = Table(main_table_data, colWidths=[page_width*0.4, page_width*0.3, page_width*0.3])
    main_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(main_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Routes
@api_router.post("/auth/login")
async def login(user_login: UserLogin):
    user = await db.users.find_one({"email": user_login.email})
    if not user or not verify_password(user_login.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
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
    
    await db.users.insert_one(user.dict())
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

@api_router.post("/timesheets", response_model=WeeklyTimesheet)
async def create_timesheet(timesheet_create: WeeklyTimesheetCreate, current_user: User = Depends(get_current_user)):
    # Calculate week end (Sunday)
    from datetime import datetime, timedelta
    week_start = datetime.strptime(timesheet_create.week_start, "%Y-%m-%d")
    week_end = week_start + timedelta(days=6)
    
    timesheet = WeeklyTimesheet(
        user_id=current_user.id,
        user_name=current_user.name,
        week_start=timesheet_create.week_start,
        week_end=week_end.strftime("%Y-%m-%d"),
        entries=timesheet_create.entries
    )
    
    await db.timesheets.insert_one(timesheet.dict())
    return timesheet

@api_router.get("/timesheets", response_model=List[WeeklyTimesheet])
async def get_timesheets(current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        timesheets = await db.timesheets.find().to_list(1000)
    else:
        timesheets = await db.timesheets.find({"user_id": current_user.id}).to_list(1000)
    
    return [WeeklyTimesheet(**timesheet) for timesheet in timesheets]

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
        update_data["entries"] = [entry.dict() for entry in timesheet_update.entries]
    
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
        
        # Update timesheet status to "sent"
        await db.timesheets.update_one(
            {"id": timesheet_id},
            {"$set": {"status": "sent"}}
        )
        
        return {"message": "Email sent successfully"}
    
    except Exception as e:
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
    allow_credentials=True,
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