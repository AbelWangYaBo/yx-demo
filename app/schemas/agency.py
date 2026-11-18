from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class AgencyCreate(BaseModel):
    name: str
    uscc: str
    travel_license_no: str | None = None
    outbound_licensed: bool = False
    license_expiry: date | None = None
    filing_status: str = "未备案"
    filing_no: str | None = None
    filing_date: date | None = None
    premise_proof: str | None = None
    policy_documents: list[str] | None = None


class AgencyUpdate(BaseModel):
    name: str | None = None
    uscc: str | None = None
    travel_license_no: str | None = None
    outbound_licensed: bool | None = None
    license_expiry: date | None = None
    filing_status: str | None = None
    filing_no: str | None = None
    filing_date: date | None = None
    premise_proof: str | None = None
    policy_documents: list[str] | None = None


class AgencyOut(AgencyCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: object
    updated_at: object


class StaffCreate(BaseModel):
    agency_id: int
    name: str
    role: str
    id_card_masked: str | None = None
    no_crime_declaration: bool = False
    filing_status: str = "未备案"
    filing_date: date | None = None
    expiry_date: date | None = None


class StaffUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    id_card_masked: str | None = None
    no_crime_declaration: bool | None = None
    filing_status: str | None = None
    filing_date: date | None = None
    expiry_date: date | None = None


class StaffOut(StaffCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
