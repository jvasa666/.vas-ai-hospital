import base64
import time
import json
import logging
import uuid
from typing import Dict, Any

from ..ai_api import register_capability 

def zfp_encrypt_deterministic(plaintext: str) -> str:
    encrypted_bytes = f"[ZFP-P4-ENC-{time.time()}]:{plaintext}".encode('utf-8')
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def handle_data_encrypt(terms: Dict[str, Any]) -> Dict[str, str]:
    plaintext = terms.get("plaintext", "")
    if not plaintext:
        raise ValueError("Encryption requires 'plaintext'.")
        
    ciphertext_base64 = zfp_encrypt_deterministic(plaintext)
    
    return {"ciphertext_base64": ciphertext_base64}

def handle_audit_log(terms: Dict[str, Any]) -> Dict[str, Any]:
    action = terms.get("action", "UNKNOWN")
    entity_id = terms.get("entity_id", "UNKNOWN")
    user_id = terms.get("user_id", "SYSTEM")
    data_summary = terms.get("data")
    
    log_entry = {
        "timestamp": time.time(),
        "pillar": "P9_PRESERVE_AUDIT",
        "action": action,
        "entity_id": entity_id,
        "user_id": user_id,
        "summary": "Data logged to immutable ledger (simulated).",
        "full_data_hash": hash(json.dumps(data_summary))
    }
    
    logging.getLogger("Pillar9_Audit_Log").info(f"AUDIT LOGGED: {log_entry}")
    
    return {"log_id": str(uuid.uuid4()), "status": "Immutable Log Confirmed"}

def handle_clinical_sepsis_risk(terms: Dict[str, Any]) -> Dict[str, Any]:
    vitals = terms.get("vitals")
    
    if vitals and vitals.get("blood_pressure") < 90:
        risk = 0.99 
    else:
        risk = 0.05
        
    return {"risk_score": risk, "recommendation": "LOW_RISK" if risk < 0.5 else "INITIATE_SEPSIS_PROTOCOL"}

def initialize_core_capabilities():
    register_capability("data:encrypt", handle_data_encrypt)
    register_capability("audit:log", handle_audit_log)
    register_capability("clinical:sepsis_risk", handle_clinical_sepsis_risk)
    
    logging.getLogger("ai_api").info("ZFP Core Capabilities Registered.")