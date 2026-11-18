"""Pydantic 请求/响应 Schema（按模块分文件，此为汇总入口）。"""
from app.schemas.agency import AgencyOut, AgencyUpdate, AgencyCreate, StaffCreate, StaffOut, StaffUpdate
from app.schemas.audit import AuditOut, AuditPage, VerifyOut
from app.schemas.consent import ConsentCreate, ConsentOut
from app.schemas.contract import ContractCreate, ContractOut, RefundQuoteIn, RefundQuoteOut
from app.schemas.document import CommunicationCreate, CommunicationOut, DocumentCreate, DocumentOut
from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut
from app.schemas.payment import PaymentCreate, PaymentOut
from app.schemas.program import ProgramCreate, ProgramOut, ProgramUpdate
from app.schemas.quotation import QuotationCreate, QuotationOut, QuotePreviewIn
from app.schemas.school import CourseCreate, CourseOut, CourseUpdate, SchoolCreate, SchoolOut, SchoolUpdate
from app.schemas.service_event import ServiceEventCreate, ServiceEventOut
from app.schemas.student import StudentCreate, StudentOut
from app.schemas.weekly_report import WeeklyReportCreate, WeeklyReportOut

__all__ = [
    "AgencyCreate", "AgencyOut", "AgencyUpdate",
    "StaffCreate", "StaffOut", "StaffUpdate",
    "StudentCreate", "StudentOut",
    "ConsentCreate", "ConsentOut",
    "ProgramCreate", "ProgramOut", "ProgramUpdate",
    "EnrollmentCreate", "EnrollmentOut",
    "ContractCreate", "ContractOut", "RefundQuoteIn", "RefundQuoteOut",
    "PaymentCreate", "PaymentOut",
    "ServiceEventCreate", "ServiceEventOut",
    "DocumentCreate", "DocumentOut", "CommunicationCreate", "CommunicationOut",
    "AuditOut", "AuditPage", "VerifyOut",
    "SchoolCreate", "SchoolOut", "SchoolUpdate",
    "CourseCreate", "CourseOut", "CourseUpdate",
    "QuotationCreate", "QuotationOut", "QuotePreviewIn",
    "WeeklyReportCreate", "WeeklyReportOut",
]
