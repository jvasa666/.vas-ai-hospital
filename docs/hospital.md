Enterprise Architecture & Design Document - ZFP CAUSAL ANCHOR EDITION
Executive Summary
This document outlines a modern, cloud-native hospital management system designed for:
Deterministic Control: Future state anchored by ZFP Causal Nexus Anchor (CNA).
Scalability: Handle 10,000+ concurrent users
Security: HIPAA/GDPR compliant, enforced by ZFP Pillar 4 (Encrypt).
Reliability: 99.99% uptime SLA
Interoperability: HL7 FHIR, DICOM, and standard EHR integration
AI-Powered: All critical analytics and clinical support routed through ZFP AI-API Layer.
Real-time: WebSocket-based updates for critical events
System Architecture
High-Level Architecture (ZFP-Anchored)
┌──────────────────────────────────────────────────────────────────┐
│ API Gateway Layer │
│ (Kong/AWS API Gateway + Auth + AI-API Client) │
└──────────────────────────┬────────────────────────────────────────┘
│
┌──────────────────────┼───────────────────────┐
│ │ │
┌───▼────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌────▼─────┐
│Patient │ │Clinical │ │Admin │ │Analytics │
│Service │ │Service │ │Service │ │Service │
└───┬────┘ └─────┬─────┘ └─────┬─────┘ └────┬─────┘
│ │ │ │
│ ZFP AI-API CLIENTS (Negotiate Capability)
│ │ │ │
└─────────────▼───────────────▼──────────────┘
│
┌───────────────────▼──────────────────┐
│ ZFP AI-API LAYER (Capability Router) │ ← All Cross-Cutting & AI Calls Route HERE
│ (ai_api.py Instance + Capability Handlers) │ (e.g., data:encrypt, audit:log, clinical:risk_score)
└───────────────────┬──────────────────┘
│
┌───────────────┼───────────────────────┐
│ │ │
┌───▼────┐ ┌───────▼───────┐ ┌─────────────┐ ┌─────────────┐
│Patient │ │Clinical/ML │ │Audit/Ledger │ │File Storage │
│DB (PG) │ │DB (PG/Mongo) │ │DB (TimescaleDB)│ │(S3/MinIO) │
└────────┘ └───────────────┘ └─────────────┘ └─────────────┘
code
Code
Core Microservices (Revised Role)
1. Patient Management Service
Role: Becomes a Capability Orchestrator
Changes: Relies on AI-API for:
Encryption (Pillar 4): Calls data:encrypt for SSN/Insurance.
Auditing (Pillar 9): Calls audit:log_patient_creation.
2. Clinical Service
Role: Becomes a Capability Consumer and Publisher
Changes:
CDSS (Pillar 13): Calls clinical:sepsis_risk (via AI-API) instead of local ML model.
AI-API Registration: Registers itself as the handler for the capability clinical:sepsis_risk if it is hosting the ML model, OR calls a dedicated ML Capability Service through the AI-API.
4. Analytics & Reporting Service
Role: Becomes a Capability Provider
Changes: Registers capabilities like analytics:readmission_risk and analytics:capacity_forecast with the AI-API.
AI/ML Integration (ZFP Capability Focus)
AI/ML Functions become AI-API Capabilities:
All critical AI/ML logic is externalized to dedicated capability handlers, registered with the AI-API. This centralizes control under ZFP Pillar 10 (Govern).
ZFP Capability Name	ZFP Pillar	Function	Description
data:encrypt	Pillar 4 (Encrypt)	Data Security	Encrypts/Decrypts PHI for all services.
audit:log	Pillar 9 (Preserve)	Immutable Logging	Logs every access and change to the immutable ledger.
clinical:sepsis_risk	Pillar 13 (Empathy/Infer)	Predictive Diagnosis	Predicts sepsis risk 6 hours ahead (via AI-API negotiation).
clinical:drug_interaction	Pillar 13 (Empathy/Infer)	Clinical Safety	Checks complex drug-drug interactions.
analytics:readmission_risk	Pillar 5 (Observe)	Operational Prediction	Forecasts 30-day readmission risk for intervention.
code
Python
# The ML Capability Service (running adjacent to ai_api) now hosts and registers:
from ai_api import register_capability

def handle_sepsis_risk(terms: dict) -> dict:
    # Logic is now in the dedicated ML model runner service
    patient_vitals = terms.get("vitals")
    # ... ML inference logic ...
    return {"risk_score": 0.85, "recommendation": "Initiate Sepsis Protocol"}

register_capability("clinical:sepsis_risk", handle_sepsis_risk)
code
Code
