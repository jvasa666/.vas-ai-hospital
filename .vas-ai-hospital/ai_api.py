#!/usr/bin/env python3
"""
VAS-AI-Gateway - ZFP Causal Anchor Capability Router
====================================================
The central nervous system for .vas-ai-hospital

All cross-cutting concerns (encryption, audit, ML inference) route through here.
Implements ZFP Pillars 4, 5, 9, 10, 13.
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
from cryptography.fernet import Fernet
import anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] VAS-AI-GATEWAY | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================

class Config:
    """VAS-AI-Gateway Configuration"""
    PORT = int(os.getenv("PORT", 8888))
    REDIS_HOST = os.getenv("REDIS_HOST", "vas-redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ZFP_MODE = os.getenv("ZFP_MODE", "PRODUCTION")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # Optional for AI calls

config = Config()

# ==========================================
# DATA MODELS
# ==========================================

class ZFPPillar(str, Enum):
    """ZFP Framework Pillars"""
    ENCRYPT = "encrypt"      # Pillar 4
    OBSERVE = "observe"      # Pillar 5
    PRESERVE = "preserve"    # Pillar 9
    GOVERN = "govern"        # Pillar 10
    EMPATHY = "empathy"      # Pillar 13 (AI/ML)

class CapabilityRequest(BaseModel):
    """Standard capability invocation request"""
    capability: str = Field(..., description="Capability name (e.g., 'data:encrypt')")
    terms: Dict[str, Any] = Field(default_factory=dict, description="Input parameters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    pillar: Optional[ZFPPillar] = Field(None, description="ZFP Pillar classification")

class CapabilityResponse(BaseModel):
    """Standard capability response"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    pillar: Optional[ZFPPillar] = None
    execution_time_ms: float
    timestamp: str

# ==========================================
# CAPABILITY REGISTRY
# ==========================================

class CapabilityRegistry:
    """
    Central registry for all system capabilities.
    Implements ZFP Pillar 10 (Govern) - all capabilities are discoverable and auditable.
    """
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    def register(
        self, 
        name: str, 
        handler: Callable, 
        pillar: ZFPPillar,
        description: str = ""
    ):
        """Register a capability handler"""
        self.handlers[name] = handler
        self.metadata[name] = {
            "pillar": pillar.value,
            "description": description,
            "registered_at": datetime.utcnow().isoformat()
        }
        logger.info(f"✓ Registered capability: {name} (Pillar: {pillar.value})")
    
    def get_handler(self, name: str) -> Optional[Callable]:
        """Get capability handler"""
        return self.handlers.get(name)
    
    def list_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """List all registered capabilities"""
        return self.metadata

# Global registry
registry = CapabilityRegistry()

# ==========================================
# ZFP PILLAR 4: ENCRYPTION
# ==========================================

class EncryptionService:
    """Handles all PHI encryption/decryption (ZFP Pillar 4)"""
    
    def __init__(self):
        self.cipher = Fernet(config.ENCRYPTION_KEY.encode() if isinstance(config.ENCRYPTION_KEY, str) else config.ENCRYPTION_KEY)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(ciphertext.encode()).decode()

encryption_service = EncryptionService()

async def handle_data_encrypt(terms: Dict[str, Any]) -> Dict[str, Any]:
    """Capability: data:encrypt"""
    plaintext = terms.get("plaintext")
    if not plaintext:
        raise ValueError("Missing 'plaintext' in terms")
    
    ciphertext = encryption_service.encrypt(plaintext)
    return {"ciphertext": ciphertext}

async def handle_data_decrypt(terms: Dict[str, Any]) -> Dict[str, Any]:
    """Capability: data:decrypt"""
    ciphertext = terms.get("ciphertext")
    if not ciphertext:
        raise ValueError("Missing 'ciphertext' in terms")
    
    plaintext = encryption_service.decrypt(ciphertext)
    return {"plaintext": plaintext}

# ==========================================
# ZFP PILLAR 9: AUDIT LOGGING
# ==========================================

class AuditLogger:
    """Immutable audit logging (ZFP Pillar 9)"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def log_event(
        self, 
        event_type: str, 
        actor: str, 
        resource: str, 
        action: str,
        details: Dict[str, Any] = None
    ):
        """Log an audit event to Redis (append-only)"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "actor": actor,
            "resource": resource,
            "action": action,
            "details": details or {}
        }
        
        # Store in Redis list (append-only)
        await self.redis.rpush("audit:log", json.dumps(event))
        
        # Also store with TTL for quick lookups
        event_id = f"audit:{event_type}:{datetime.utcnow().timestamp()}"
        await self.redis.setex(event_id, 86400 * 30, json.dumps(event))  # 30 days
        
        logger.info(f"AUDIT: {event_type} | {actor} -> {resource} ({action})")

# Global audit logger (initialized after Redis connection)
audit_logger: Optional[AuditLogger] = None

async def handle_audit_log(terms: Dict[str, Any]) -> Dict[str, Any]:
    """Capability: audit:log"""
    if not audit_logger:
        raise RuntimeError("Audit logger not initialized")
    
    await audit_logger.log_event(
        event_type=terms.get("event_type", "GENERIC"),
        actor=terms.get("actor", "SYSTEM"),
        resource=terms.get("resource", "UNKNOWN"),
        action=terms.get("action", "UNKNOWN"),
        details=terms.get("details", {})
    )
    
    return {"logged": True}

# ==========================================
# ZFP PILLAR 13: AI/ML CAPABILITIES
# ==========================================

class MLInferenceService:
    """AI/ML inference capabilities (ZFP Pillar 13 - Empathy)"""
    
    def __init__(self):
        self.client = None
        if config.ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    
    async def predict_sepsis_risk(self, vitals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict sepsis risk from patient vitals.
        In production, this would call a trained ML model.
        """
        # Mock implementation - replace with real ML model
        temp = vitals.get("temperature", 98.6)
        hr = vitals.get("heart_rate", 80)
        bp_sys = vitals.get("bp_systolic", 120)
        wbc = vitals.get("wbc_count", 7.5)
        
        # Simple heuristic scoring (replace with real model)
        risk_score = 0.0
        if temp > 100.4 or temp < 96.8:
            risk_score += 0.3
        if hr > 90:
            risk_score += 0.2
        if bp_sys < 100:
            risk_score += 0.3
        if wbc > 12 or wbc < 4:
            risk_score += 0.2
        
        risk_level = "LOW"
        if risk_score > 0.6:
            risk_level = "HIGH"
        elif risk_score > 0.3:
            risk_level = "MEDIUM"
        
        recommendation = "Continue monitoring"
        if risk_level == "HIGH":
            recommendation = "INITIATE SEPSIS PROTOCOL - Alert physician immediately"
        elif risk_level == "MEDIUM":
            recommendation = "Increase monitoring frequency, consider blood cultures"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "confidence": 0.85
        }
    
    async def check_drug_interactions(self, medications: list) -> Dict[str, Any]:
        """Check for drug-drug interactions"""
        # Mock implementation
        interactions = []
        
        # Simple rule-based check (replace with real drug interaction DB)
        dangerous_combos = [
            (("warfarin", "aspirin"), "Increased bleeding risk"),
            (("metformin", "iodinated_contrast"), "Lactic acidosis risk"),
            (("ssri", "tramadol"), "Serotonin syndrome risk")
        ]
        
        med_names = [m.lower() for m in medications]
        
        for combo, warning in dangerous_combos:
            if all(drug in ' '.join(med_names) for drug in combo):
                interactions.append({
                    "drugs": list(combo),
                    "severity": "HIGH",
                    "warning": warning
                })
        
        return {
            "has_interactions": len(interactions) > 0,
            "interactions": interactions,
            "checked_medications": medications
        }

ml_service = MLInferenceService()

async def handle_clinical_sepsis_risk(terms: Dict[str, Any]) -> Dict[str, Any]:
    """Capability: clinical:sepsis_risk"""
    vitals = terms.get("vitals")
    if not vitals:
        raise ValueError("Missing 'vitals' in terms")
    
    return await ml_service.predict_sepsis_risk(vitals)

async def handle_clinical_drug_interaction(terms: Dict[str, Any]) -> Dict[str, Any]:
    """Capability: clinical:drug_interaction"""
    medications = terms.get("medications")
    if not medications:
        raise ValueError("Missing 'medications' in terms")
    
    return await ml_service.check_drug_interactions(medications)

# ==========================================
# ZFP PILLAR 5: ANALYTICS/OBSERVATION
# ==========================================

async def handle_analytics_readmission_risk(terms: Dict[str, Any]) -> Dict[str, Any]:
    """Capability: analytics:readmission_risk"""
    patient_data = terms.get("patient_data", {})
    
    # Mock prediction - replace with real model
    risk_factors = []
    risk_score = 0.0
    
    age = patient_data.get("age", 0)
    if age > 65:
        risk_score += 0.3
        risk_factors.append("Age > 65")
    
    if patient_data.get("chronic_conditions", 0) > 2:
        risk_score += 0.4
        risk_factors.append("Multiple chronic conditions")
    
    if patient_data.get("previous_admissions_30d", 0) > 0:
        risk_score += 0.3
        risk_factors.append("Recent admission")
    
    return {
        "risk_score": min(risk_score, 1.0),
        "risk_level": "HIGH" if risk_score > 0.6 else "MEDIUM" if risk_score > 0.3 else "LOW",
        "risk_factors": risk_factors,
        "recommendation": "Consider discharge planning intervention" if risk_score > 0.6 else "Standard discharge protocol"
    }

# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="VAS-AI-Gateway",
    description="ZFP Causal Anchor Capability Router for .vas-ai-hospital",
    version="1.0.0"
)

# Redis connection pool
redis_pool: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global redis_pool, audit_logger
    
    logger.info("=" * 60)
    logger.info("VAS-AI-GATEWAY STARTING")
    logger.info("=" * 60)
    
    # Connect to Redis
    try:
        redis_pool = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
            decode_responses=True
        )
        await redis_pool.ping()
        logger.info("✓ Redis connection established")
        
        # Initialize audit logger
        audit_logger = AuditLogger(redis_pool)
        
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        redis_pool = None
    
    # Register all capabilities
    registry.register("data:encrypt", handle_data_encrypt, ZFPPillar.ENCRYPT, "Encrypt sensitive PHI data")
    registry.register("data:decrypt", handle_data_decrypt, ZFPPillar.ENCRYPT, "Decrypt sensitive PHI data")
    registry.register("audit:log", handle_audit_log, ZFPPillar.PRESERVE, "Log immutable audit events")
    registry.register("clinical:sepsis_risk", handle_clinical_sepsis_risk, ZFPPillar.EMPATHY, "Predict sepsis risk from vitals")
    registry.register("clinical:drug_interaction", handle_clinical_drug_interaction, ZFPPillar.EMPATHY, "Check drug-drug interactions")
    registry.register("analytics:readmission_risk", handle_analytics_readmission_risk, ZFPPillar.OBSERVE, "Predict 30-day readmission risk")
    
    logger.info(f"✓ Registered {len(registry.handlers)} capabilities")
    logger.info("VAS-AI-GATEWAY READY")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if redis_pool:
        await redis_pool.close()
    logger.info("VAS-AI-GATEWAY SHUTDOWN")

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "UP",
        "service": "vas-ai-gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "redis_connected": redis_pool is not None
    }

@app.get("/capabilities")
async def list_capabilities():
    """List all registered capabilities"""
    return {
        "capabilities": registry.list_capabilities(),
        "total": len(registry.handlers)
    }

@app.post("/invoke", response_model=CapabilityResponse)
async def invoke_capability(request: CapabilityRequest):
    """
    Invoke a capability by name.
    This is the main entry point for all capability execution.
    """
    start_time = datetime.utcnow()
    
    # Get handler
    handler = registry.get_handler(request.capability)
    if not handler:
        raise HTTPException(
            status_code=404, 
            detail=f"Capability '{request.capability}' not found"
        )
    
    try:
        # Execute capability
        result = await handler(request.terms)
        
        # Log to audit trail
        if audit_logger:
            await audit_logger.log_event(
                event_type="CAPABILITY_INVOKE",
                actor=request.context.get("user_id", "SYSTEM"),
                resource=request.capability,
                action="EXECUTE",
                details={"terms": request.terms}
            )
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return CapabilityResponse(
            success=True,
            result=result,
            pillar=request.pillar,
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Capability execution failed: {request.capability} | {str(e)}")
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return CapabilityResponse(
            success=False,
            error=str(e),
            pillar=request.pillar,
            execution_time_ms=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "VAS-AI-Gateway",
        "version": "1.0.0",
        "description": "ZFP Causal Anchor Capability Router",
        "endpoints": {
            "health": "/health",
            "capabilities": "/capabilities",
            "invoke": "/invoke (POST)"
        }
    }

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "ai_api:app",
        host="0.0.0.0",
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower(),
        access_log=True
    )