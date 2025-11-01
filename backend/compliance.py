"""
DSGVO und EU-AI-Act Compliance Module
Sicherstellung der Datenschutz-Compliance für Reisekostenabrechnungen
"""

import os
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

# DSGVO Aufbewahrungsfristen (in Tagen)
# Reisekostenbelege: 10 Jahre gemäß GoBD
RETENTION_PERIOD_RECEIPTS_DAYS = 10 * 365  # 10 Jahre
# Abgelehnte/entworfene Abrechnungen: 1 Jahr
RETENTION_PERIOD_DRAFT_DAYS = 365
# Genehmigte Abrechnungen: 10 Jahre
RETENTION_PERIOD_APPROVED_DAYS = 10 * 365

class DataEncryption:
    """Verschlüsselung für sensible Dokumente (DSGVO Art. 32)"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption with key from environment or generate new key
        WARNING: Encryption key must be stored securely and never committed to repository
        """
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # Get key from environment or generate warning
            env_key = os.getenv('ENCRYPTION_KEY')
            if env_key:
                self.key = env_key.encode()
            else:
                logger.warning("ENCRYPTION_KEY not set - using temporary key (NOT SECURE FOR PRODUCTION)")
                # Generate temporary key (only for development)
                self.key = Fernet.generate_key()
        
        # Derive a proper Fernet key from the provided key
        if len(self.key) != 44:  # Fernet keys are 44 bytes base64 encoded
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'dsgvo_compliance_salt',  # In production, use random salt per file
                iterations=100000,
            )
            key_material = kdf.derive(self.key)
            self.key = base64.urlsafe_b64encode(key_material)
        
        self.cipher = Fernet(self.key)
    
    def encrypt_file(self, file_path: Path) -> bool:
        """Encrypt a file in place"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = self.cipher.encrypt(data)
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            return True
        except Exception as e:
            logger.error(f"Error encrypting file {file_path}: {e}")
            return False
    
    def decrypt_file(self, file_path: Path) -> bytes:
        """Decrypt a file and return content"""
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data
        except Exception as e:
            logger.error(f"Error decrypting file {file_path}: {e}")
            raise
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        """Encrypt bytes data"""
        return self.cipher.encrypt(data)
    
    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """Decrypt bytes data"""
        return self.cipher.decrypt(encrypted_data)

class AuditLogger:
    """Audit-Logging für DSGVO-Compliance (Art. 5 Abs. 2)"""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path(__file__).parent / "logs" / "audit.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_access(self, action: str, user_id: str, resource_type: str, resource_id: str, 
                   details: Optional[Dict] = None):
        """Log data access for compliance"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,  # "view", "download", "delete", "upload", "modify"
            "user_id": user_id,
            "resource_type": resource_type,  # "receipt", "report", "document"
            "resource_id": resource_id,
            "details": details or {}
        }
        
        # Write to audit log file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Error writing to audit log: {e}")

class RetentionManager:
    """Verwaltung von Aufbewahrungsfristen (DSGVO Art. 5 Abs. 1 e)"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_files_to_delete(self) -> List[Dict[str, Any]]:
        """Get files that exceed retention period and should be deleted"""
        files_to_delete = []
        
        # Get all expense reports
        async for report in self.db.travel_expense_reports.find({}):
            report_date = report.get("created_at")
            if not report_date:
                continue
            
            if isinstance(report_date, str):
                report_date = datetime.fromisoformat(report_date.replace('Z', '+00:00'))
            
            days_old = (datetime.utcnow() - report_date.replace(tzinfo=None)).days
            
            # Determine retention period based on status
            status = report.get("status", "draft")
            if status == "approved":
                retention_days = RETENTION_PERIOD_APPROVED_DAYS
            elif status == "draft":
                retention_days = RETENTION_PERIOD_DRAFT_DAYS
            else:
                retention_days = RETENTION_PERIOD_RECEIPTS_DAYS
            
            if days_old > retention_days:
                # Mark receipts for deletion
                receipts = report.get("receipts", [])
                for receipt in receipts:
                    files_to_delete.append({
                        "report_id": report.get("id"),
                        "receipt_id": receipt.get("id"),
                        "local_path": receipt.get("local_path"),
                        "reason": f"Retention period exceeded ({days_old} days old, max {retention_days} days)",
                        "report_status": status
                    })
        
        return files_to_delete
    
    async def delete_expired_files(self, encryption: Optional[DataEncryption] = None):
        """Delete files that exceed retention period"""
        files_to_delete = await self.get_files_to_delete()
        deleted_count = 0
        
        for file_info in files_to_delete:
            local_path = Path(file_info["local_path"])
            if local_path.exists():
                try:
                    # Decrypt if encrypted
                    if encryption:
                        try:
                            encryption.decrypt_file(local_path)
                        except:
                            pass  # File might not be encrypted
                    
                    local_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted expired file: {local_path} - {file_info['reason']}")
                except Exception as e:
                    logger.error(f"Error deleting expired file {local_path}: {e}")
        
        return deleted_count

class AITransparency:
    """EU-AI-Act Compliance: Transparenz bei AI-Entscheidungen"""
    
    @staticmethod
    def create_ai_decision_log(decision_type: str, agent_name: str, input_data: Dict, 
                               output_data: Dict, confidence: float, 
                               human_reviewed: bool = False) -> Dict[str, Any]:
        """Create log entry for AI decision (Art. 13 EU-AI-Act)"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "decision_type": decision_type,  # "document_analysis", "expense_assignment", "validation"
            "agent_name": agent_name,
            "ai_model": os.getenv('OLLAMA_MODEL', 'llama3.2'),
            "input_data_hash": hashlib.sha256(str(input_data).encode()).hexdigest(),  # Privacy-preserving hash
            "output_summary": {
                "result": output_data.get("result") if isinstance(output_data, dict) else str(output_data)[:500],
                "confidence": confidence,
                "key_factors": output_data.get("key_factors", []) if isinstance(output_data, dict) else []
            },
            "human_reviewed": human_reviewed,
            "compliance_note": "AI-Entscheidung gemäß EU-AI-Act Art. 13 - Benutzer hat Recht auf Auskunft über Entscheidungsgrundlagen"
        }
    
    @staticmethod
    def create_user_notification(report_id: str, ai_decision: Dict) -> str:
        """Create user-friendly notification about AI decision"""
        return f"""AI-Entscheidung für Ihre Reisekostenabrechnung:

Agent: {ai_decision['agent_name']}
Entscheidung: {ai_decision['decision_type']}
Konfidenz: {ai_decision['output_summary']['confidence']:.0%}
Menschlich geprüft: {'Ja' if ai_decision['human_reviewed'] else 'Nein (automatisch)'}

Sie haben gemäß EU-AI-Act das Recht auf:
- Auskunft über die Entscheidungsgrundlagen
- Widerspruch gegen die Entscheidung
- Menschliche Überprüfung

Bei Fragen kontaktieren Sie bitte den Administrator."""

def validate_local_storage_path(storage_path: str) -> tuple[bool, str]:
    """
    Validate that storage path is local (not on webserver)
    Returns (is_valid, error_message)
    """
    path = Path(storage_path)
    
    # Check if path is absolute
    if not path.is_absolute():
        return False, "Storage path must be absolute"
    
    # Check for common webserver paths (Windows and Linux)
    webserver_indicators = [
        '/var/www/',
        '/usr/share/nginx/',
        '/srv/www/',
        'C:\\inetpub\\',
        'C:\\xampp\\',
        '/home/www/',
        '/opt/lampp/'
    ]
    
    path_str = str(path).lower().replace('\\', '/')
    for indicator in webserver_indicators:
        if indicator.lower() in path_str:
            return False, f"Storage path appears to be on webserver: {indicator}"
    
    # Check if path is on local filesystem (has drive letter on Windows or starts with / on Unix)
    if os.name == 'nt':  # Windows
        if not path_str[1:3] == ':/':
            return False, "Windows path must have drive letter (e.g., C:/)"
    else:  # Unix/Linux
        if not path_str.startswith('/'):
            return False, "Unix path must be absolute (start with /)"
    
    return True, ""

