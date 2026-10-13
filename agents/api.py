"""
FastAPI REST API Server for Specimen Rejection Analyzer.
"""
import os
import hmac
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Specimen Rejection Analyzer API",
    description="Rule-based demonstration for laboratory quality workflows",
    version="3.0.0",
)


@app.exception_handler(SecurityException)
async def blocked_identifier(request: Request, exc: SecurityException):
    return JSONResponse(status_code=422, content={"detail": "Sensitive identifier detected. Supply de-identified data."})


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "specimen-rejection-analyzer", "domain": "Clinical & Biomedical AI", "standard": "Unvalidated demonstration rules", "version": "3.0.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "AUDIT_VALID" if AuditLogger.verify_integrity() else "AUDIT_INVALID"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs(x_audit_token: str | None = Header(default=None)):
    """Audit access is disabled by default and requires a separate shared secret."""
    token = os.environ.get("API_AUDIT_TOKEN")
    if not token:
        raise HTTPException(status_code=503, detail="Audit log access is not configured")
    if x_audit_token is None or not hmac.compare_digest(x_audit_token, token):
        raise HTTPException(status_code=403, detail="Invalid audit access token")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
