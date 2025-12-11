import asyncio
import logging
import json
from typing import Callable, Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- ZFP CORE REGISTRY LOGIC ---
PROJECT_ROOT = Path("/app")
logger = logging.getLogger("ai_api")

class CapabilityError(Exception):
    pass

class CapabilityRegistry:
    def __init__(self):
        self._registry: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register(self, name: str, handler: Callable[[Dict[str, Any]], Any]):
        if name in self._registry:
            logger.warning(f"Overwriting capability registration: {name}")
        self._registry[name] = handler
        logger.info(f"Registered capability: {name}")

    def get(self, name: str) -> Optional[Callable[[Dict[str, Any]], Any]]:
        return self._registry.get(name)

_registry = CapabilityRegistry()

async def negotiate_core(capability: str, terms: Dict[str, Any]) -> Dict[str, Any]:
    handler = _registry.get(capability)
    if handler is None:
        logger.warning(f"Capability not found: {capability}")
        raise CapabilityError(f"Capability not found: {capability}")

    try:
        if asyncio.iscoroutinefunction(handler):
            result = await handler(terms)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: handler(terms))

        return {
            "status": "ok",
            "capability": capability,
            "result": result
        }
    except Exception as e:
        logger.exception("Capability invocation failed")
        return {
            "status": "error",
            "capability": capability,
            "error": str(e)
        }

def register_capability(name: str, handler: Callable[[Dict[str, Any]], Any]):
    _registry.register(name, handler)


app = FastAPI(title="ZFP AI-API Nexus", version="1.0.0")

class NegotiateRequest(BaseModel):
    capability: str
    terms: Dict[str, Any]

@app.post("/negotiate")
async def negotiate_endpoint(request: NegotiateRequest):
    try:
        response = await negotiate_core(request.capability, request.terms)
        if response.get("status") == "error":
            raise HTTPException(status_code=500, detail=response["error"])
        return response
    except CapabilityError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "capabilities_loaded": len(_registry._registry)}

# --- LOAD CAPABILITIES ---
from capabilities.core_capabilities import initialize_core_capabilities
initialize_core_capabilities()