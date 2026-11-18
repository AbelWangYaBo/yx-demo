from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.apis.agency import router as agency_router, staff_router
from app.apis.access_api import router as access_router
from app.apis.attachments import router as attachments_router
from app.apis.audit_api import router as audit_router
from app.apis.compliance_api import router as compliance_router
from app.apis.contracts import router as contracts_router
from app.apis.consents import router as consents_router
from app.apis.documents import communications_router, documents_router
from app.apis.enrollments import router as enrollments_router
from app.apis.finance import events_router, payments_router
from app.apis.programs import router as programs_router
from app.apis.quotations import router as quotations_router
from app.apis.schools import courses_router, router as schools_router
from app.apis.students import router as students_router
from app.apis.weekly_reports import router as weekly_reports_router
from app.config import APP_PORT
from app.services.errors import ComplianceError, NotFound, StudentNotFound

app = FastAPI(
    title="游学/留学机构合规数据管理系统（演示）",
    version="0.1.0",
    description="841号令双重备案 + 操作留痕审计链 + 学员主索引归集。全部数据为虚构示例。",
)

for r in (
    agency_router, staff_router, students_router, consents_router,
    programs_router, enrollments_router, contracts_router,
    payments_router, events_router, documents_router, communications_router,
    attachments_router, access_router, audit_router, compliance_router,
    schools_router, courses_router, quotations_router, weekly_reports_router,
):
    app.include_router(r)


@app.exception_handler(StudentNotFound)
@app.exception_handler(NotFound)
async def _not_found_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ComplianceError)
async def _compliance_handler(request: Request, exc: ComplianceError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=APP_PORT)
