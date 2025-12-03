"""
API-Endpoint für Datenbank-Migration (für Web-Interface)
Ermöglicht Migration über das Admin-Panel
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
import asyncio
import logging
from migration_tool import DatabaseMigration

logger = logging.getLogger(__name__)

migration_router = APIRouter(prefix="/admin/migration", tags=["Migration"])

class SourceConfig(BaseModel):
    """Konfiguration für Source-Datenbank"""
    type: str = Field(..., description="Datenbank-Typ: 'mongo' oder 'mysql'")
    host: Optional[str] = Field(None, description="Host (für MySQL/MongoDB)")
    port: Optional[int] = Field(None, description="Port")
    database: str = Field(..., description="Datenbank-Name")
    user: Optional[str] = Field(None, description="Benutzername (MySQL)")
    password: Optional[str] = Field(None, description="Passwort (MySQL)")
    connection_string: Optional[str] = Field(None, description="MongoDB Connection String")

class TargetConfig(BaseModel):
    """Konfiguration für Target-Datenbank"""
    mongo_url: str = Field(default="mongodb://localhost:27017", description="MongoDB URL")
    db_name: str = Field(default="stundenzettel", description="Datenbank-Name")

class MigrationRequest(BaseModel):
    """Migration-Request"""
    source: SourceConfig
    target: TargetConfig = Field(default_factory=lambda: TargetConfig())
    mapping_config: Optional[Dict[str, Any]] = None
    skip_users: bool = False
    skip_timesheets: bool = False
    skip_travel_expenses: bool = False

# Globale Variable für Migration-Status
migration_status = {
    "running": False,
    "progress": None,
    "results": None,
    "error": None
}

async def run_migration_async(request: MigrationRequest):
    """Führe Migration asynchron aus"""
    global migration_status
    
    try:
        migration_status["running"] = True
        migration_status["error"] = None
        migration_status["progress"] = "Migration gestartet..."
        
        source_config = request.source.dict(exclude_none=True)
        target_config = request.target.dict()
        
        migration = DatabaseMigration(source_config, target_config)
        results = await migration.migrate_all(
            mapping_config=request.mapping_config,
            skip_users=request.skip_users,
            skip_timesheets=request.skip_timesheets,
            skip_travel_expenses=request.skip_travel_expenses
        )
        
        migration_status["results"] = results
        migration_status["progress"] = "Migration abgeschlossen"
        migration_status["running"] = False
        
        return results
        
    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        migration_status["error"] = str(e)
        migration_status["running"] = False
        migration_status["progress"] = f"Fehler: {str(e)}"
        raise

def setup_migration_router(get_admin_user_func):
    """Setup migration router with admin dependency"""
    global migration_router
    
    @migration_router.post("/start")
    async def start_migration(
        request: MigrationRequest,
        current_user = Depends(get_admin_user_func)
    ):
        """
        Startet Datenbank-Migration
        
        WICHTIG: Source-DB wird nur gelesen, niemals verändert!
        Nur für Admin-User zugänglich.
        """
        from migration_tool import DatabaseMigration
        
        global migration_status
        
        if migration_status["running"]:
            raise HTTPException(status_code=400, detail="Migration läuft bereits")
        
        # Migration in Background-Task starten
        asyncio.create_task(run_migration_async(request))
        
        return {
            "message": "Migration gestartet",
            "status": "running"
        }
    
    @migration_router.get("/status")
    async def get_migration_status(
        current_user = Depends(get_admin_user_func)
    ):
        """Aktuellen Migration-Status abrufen"""
        return migration_status
    
    @migration_router.post("/test-connection")
    async def test_source_connection(
        source: SourceConfig,
        current_user = Depends(get_admin_user_func)
    ):
        """Teste Verbindung zur Source-Datenbank (read-only)"""
        try:
            source_config = source.dict(exclude_none=True)
            target_config = {"mongo_url": "mongodb://localhost:27017", "db_name": "test"}
            
            migration = DatabaseMigration(source_config, target_config)
            await migration.connect_source()
            
            # Test-Query ausführen
            if source_config['type'] == 'mongo':
                source_db = migration.source_client[source_config.get('database')]
                # Versuche nur zu lesen
                collections = source_db.list_collection_names()
                
            elif source_config['type'] == 'mysql':
                cursor = migration.source_client.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            
            # Verbindung schließen
            if migration.source_client:
                if source_config['type'] == 'mysql':
                    migration.source_client.close()
                else:
                    migration.source_client.close()
            
            return {
                "success": True,
                "message": "Verbindung erfolgreich (read-only)"
            }
            
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            raise HTTPException(status_code=400, detail=f"Verbindung fehlgeschlagen: {str(e)}")
