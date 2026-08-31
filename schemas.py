"""Pydantic input contracts and SDL result entities for SAP Ariba Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class ConnectionRefParams(BaseModel):
    connection_id: str = Field("", description="Optional saved SAP Ariba realm connection ID. Omit to use the first connected realm.")


class ConnectAribaParams(BaseModel):
    label: str = Field("", description="Friendly realm label, e.g. 'Acme Production'.")
    realm: str = Field(..., description="SAP Ariba realm/site identifier, e.g. AN01000000042-T.")
    application_key: str = Field(..., description="OAuth2 application key issued via SAP Ariba Developer Portal.")
    application_secret: str = Field(..., description="OAuth2 application secret issued via SAP Ariba Developer Portal.")
    api_key: str = Field(..., description="SAP API Business Hub API key for the subscribed Ariba API packages.")


class DisconnectAribaParams(ConnectionRefParams):
    connection_id: str = Field(..., description="Saved SAP Ariba realm connection ID to remove from Imperal.")


class ListRequisitionsParams(ConnectionRefParams):
    status: str = Field("", description="Optional requisition status filter, e.g. Approved, Pending Approval.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetRequisitionParams(ConnectionRefParams):
    requisition_id: str = Field(..., description="Ariba requisition unique identifier.")


class CreateRequisitionParams(ConnectionRefParams):
    title: str = Field(..., description="Requisition title/description.")
    requester_email: str = Field(..., description="Email of the requester this requisition is created for.")
    lines: list[dict] = Field(..., description="List of {ItemDescription, Quantity, UnitPrice, CommodityCode} line dicts.")


class ListPurchaseOrdersParams(ConnectionRefParams):
    supplier: str = Field("", description="Optional supplier name filter.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetPurchaseOrderParams(ConnectionRefParams):
    order_id: str = Field(..., description="Ariba purchase order unique identifier.")


class ListInvoicesParams(ConnectionRefParams):
    status: str = Field("", description="Optional invoice status filter.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetInvoiceParams(ConnectionRefParams):
    invoice_id: str = Field(..., description="Ariba invoice unique identifier.")


class ListSuppliersParams(ConnectionRefParams):
    query: str = Field("", description="Optional supplier name search filter.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetSupplierParams(ConnectionRefParams):
    supplier_id: str = Field(..., description="Ariba Network ID (ANID) or internal supplier identifier.")


class ListSourcingEventsParams(ConnectionRefParams):
    status: str = Field("", description="Optional sourcing event status filter, e.g. Open, Closed.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetSourcingEventParams(ConnectionRefParams):
    event_id: str = Field(..., description="Ariba sourcing event unique identifier.")


class ListContractWorkspacesParams(ConnectionRefParams):
    status: str = Field("", description="Optional contract workspace status filter.")
    top: int = Field(50, ge=1, le=200, description="Maximum records to return (1-200).")


class GetContractWorkspaceParams(ConnectionRefParams):
    workspace_id: str = Field(..., description="Ariba contract workspace unique identifier.")


class AuditAccessParams(ConnectionRefParams):
    pass


class SAPAribaConnection(sdl.Entity):
    id: str
    title: str
    label: str
    realm: str


class ConnectionList(sdl.Entity):
    id: str = ""
    title: str = ""
    items: list[SAPAribaConnection] = Field(default_factory=list)
    total: int = 0


class AribaRecord(sdl.Entity):
    id: str
    title: str
    fields: dict = Field(default_factory=dict)


class AribaRecordList(sdl.Entity):
    id: str = ""
    title: str = ""
    items: list[AribaRecord] = Field(default_factory=list)
    total: int = 0


class Capability(sdl.Entity):
    id: str = ""
    title: str = ""
    name: str
    available: bool
    note: str


class AccessAudit(sdl.Entity):
    id: str = ""
    title: str = ""
    realm: str
    capabilities: list[Capability] = Field(default_factory=list)
    available_count: int = 0
    unavailable_count: int = 0
    checks: list[Capability] = Field(default_factory=list)


class DeleteResult(sdl.Entity):
    title: str = ""
    deleted: bool
    id: str
