"""Chat functions for the capability-aware SAP Ariba Connector.

Every handler resolves the target realm connection explicitly (by
connection_id, or the sole connection if only one exists) and never assumes
an API package is licensed before a real call confirms it.
"""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import sap_ariba_client as ac
from app import chat
from schemas import (
    AccessAudit, AuditAccessParams, Capability, ConnectionList,
    ConnectionRefParams, ConnectAribaParams, CreateRequisitionParams,
    DeleteResult, DisconnectAribaParams, GetContractWorkspaceParams,
    GetInvoiceParams, GetPurchaseOrderParams, GetRequisitionParams,
    GetSourcingEventParams, GetSupplierParams, ListContractWorkspacesParams,
    ListInvoicesParams, ListPurchaseOrdersParams, ListRequisitionsParams,
    ListSourcingEventsParams, ListSuppliersParams, NoParams,
    SAPAribaConnection, AribaRecord, AribaRecordList,
)

_SECRET_NAME = "sap_ariba_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


def _connection_entity(connection: dict) -> SAPAribaConnection:
    label = connection.get("label") or connection.get("realm", "")
    return SAPAribaConnection(
        id=connection.get("id", ""),
        title=label,
        label=label,
        realm=connection.get("realm", ""),
    )


async def _resolve_connection(ctx, connection_id: str) -> dict | None:
    connections = await _load_connections(ctx)
    if not connections:
        return None
    if connection_id:
        for connection in connections:
            if connection.get("id") == connection_id:
                return connection
        return None
    return connections[0]


async def _no_connection_error() -> ActionResult:
    return ActionResult.error("No SAP Ariba realm is connected yet. Use connect_ariba first.", code="SAP_ARIBA_NOT_CONNECTED")


def _client_from(connection: dict) -> ac.SAPAribaClient:
    return ac.SAPAribaClient(
        realm=connection.get("realm", ""),
        application_key=connection.get("application_key", ""),
        application_secret=connection.get("application_secret", ""),
        api_key=connection.get("api_key", ""),
    )


def _record(body: dict, id_key: str, title_keys: list[str]) -> AribaRecord:
    rid = str(body.get(id_key, ""))
    title = ""
    for key in title_keys:
        if body.get(key):
            title = str(body.get(key))
            break
    return AribaRecord(id=rid, title=title or rid, fields=body)


@chat.function("connect_ariba", "Connect a SAP Ariba realm (OAuth2 client credentials), after validating connectivity.", action_type="write", chain_callable=True, data_model=SAPAribaConnection, event="sap-ariba-connector.connect_ariba", effects=["sap_ariba.provider.connected"])
async def connect_ariba(ctx, params: ConnectAribaParams) -> ActionResult:
    """Imperal action: connect_ariba."""
    client = ac.SAPAribaClient(
        realm=params.realm,
        application_key=params.application_key,
        application_secret=params.application_secret,
        api_key=params.api_key,
    )
    try:
        await client.ping()
    except ac.SAPAribaError as exc:
        return ActionResult.error(str(exc), code="SAP_ARIBA_CONNECT_FAILED", retryable=exc.retryable)

    connections = await _load_connections(ctx)
    record = {
        "id": str(uuid.uuid4()),
        "label": params.label or params.realm,
        "realm": params.realm,
        "application_key": params.application_key,
        "application_secret": params.application_secret,
        "api_key": params.api_key,
    }
    connections.append(record)
    await _save_connections(ctx, connections)
    return ActionResult.ok(_connection_entity(record))


@chat.function("disconnect_ariba", "Disconnect one SAP Ariba realm: deletes only the credentials saved in Imperal. Nothing is changed in Ariba.", action_type="write", chain_callable=True, data_model=DeleteResult, event="sap-ariba-connector.disconnect_ariba", effects=["sap_ariba.provider.disconnected"])
async def disconnect_ariba(ctx, params: DisconnectAribaParams) -> ActionResult:
    """Imperal action: disconnect_ariba."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error("Connection not found.", code="SAP_ARIBA_CONNECTION_NOT_FOUND")
    await _save_connections(ctx, remaining)
    return ActionResult.ok(DeleteResult(deleted=True, id=params.connection_id))


@chat.function("list_connections", "List the connected SAP Ariba realms.", action_type="read", chain_callable=True, data_model=ConnectionList, event="sap-ariba-connector.list_connections")
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """Imperal action: list_connections."""
    connections = await _load_connections(ctx)
    items = [_connection_entity(c) for c in connections]
    return ActionResult.ok(ConnectionList(items=items, total=len(items)))


async def _list_resource(ctx, params, path: str, id_key: str, title_keys: list[str], extra_params: dict | None = None) -> ActionResult:
    connection = await _resolve_connection(ctx, params.connection_id)
    if not connection:
        return await _no_connection_error()
    client = _client_from(connection)
    request_params = {"$top": params.top}
    if extra_params:
        request_params.update(extra_params)
    try:
        body = await client.request("get", path, params=request_params)
    except ac.SAPAribaError as exc:
        return ActionResult.error(str(exc), code="SAP_ARIBA_REQUEST_FAILED", retryable=exc.retryable)
    records = [_record(item, id_key, title_keys) for item in ac.rest_items(body)]
    return ActionResult.ok(AribaRecordList(items=records, total=len(records)))


async def _get_resource(ctx, params, path: str, id_key: str, title_keys: list[str]) -> ActionResult:
    connection = await _resolve_connection(ctx, params.connection_id)
    if not connection:
        return await _no_connection_error()
    client = _client_from(connection)
    try:
        body = await client.request("get", path)
    except ac.SAPAribaError as exc:
        return ActionResult.error(str(exc), code="SAP_ARIBA_REQUEST_FAILED", retryable=exc.retryable)
    return ActionResult.ok(_record(body, id_key, title_keys))


@chat.function("list_requisitions", "List Requisitions (Approvable APIs), optionally filtered by status.", action_type="read", chain_callable=True, data_model=AribaRecordList, event="sap-ariba-connector.list_requisitions")
async def list_requisitions(ctx, params: ListRequisitionsParams) -> ActionResult:
    """Imperal action: list_requisitions."""
    extra = {"status": params.status} if params.status else None
    return await _list_resource(ctx, params, "/api/requisitioning/v1/prod/requisitions", "id", ["title", "Title"], extra)


@chat.function("get_requisition", "Read one Requisition in full by its unique identifier.", action_type="read", chain_callable=True, data_model=AribaRecord, event="sap-ariba-connector.get_requisition")
async def get_requisition(ctx, params: GetRequisitionParams) -> ActionResult:
    """Imperal action: get_requisition."""
    return await _get_resource(ctx, params, f"/api/requisitioning/v1/prod/requisitions/{params.requisition_id}", "id", ["title", "Title"])


@chat.function("create_requisition", "Create a new Requisition with line items.", action_type="write", chain_callable=True, data_model=AribaRecord, event="sap-ariba-connector.create_requisition", effects=["sap_ariba.requisition.created"])
async def create_requisition(ctx, params: CreateRequisitionParams) -> ActionResult:
    """Imperal action: create_requisition."""
    connection = await _resolve_connection(ctx, params.connection_id)
    if not connection:
        return await _no_connection_error()
    client = _client_from(connection)
    payload = {"title": params.title, "requesterEmail": params.requester_email, "lines": params.lines}
    try:
        body = await client.request("post", "/api/requisitioning/v1/prod/requisitions", json_body=payload)
    except ac.SAPAribaError as exc:
        return ActionResult.error(str(exc), code="SAP_ARIBA_REQUEST_FAILED", retryable=exc.retryable)
    return ActionResult.ok(_record(body, "id", ["title", "Title"]))


@chat.function("list_purchase_orders", "List Purchase Orders (Approvable APIs), optionally filtered by supplier.", action_type="read", chain_callable=True, data_model=AribaRecordList, event="sap-ariba-connector.list_purchase_orders")
async def list_purchase_orders(ctx, params: ListPurchaseOrdersParams) -> ActionResult:
    """Imperal action: list_purchase_orders."""
    extra = {"supplier": params.supplier} if params.supplier else None
    return await _list_resource(ctx, params, "/api/order-invoice-status/v1/prod/purchaseorders", "id", ["title", "Title", "poNumber"], extra)


@chat.function("get_purchase_order", "Read one Purchase Order in full by its unique identifier.", action_type="read", chain_callable=True, data_model=AribaRecord, event="sap-ariba-connector.get_purchase_order")
async def get_purchase_order(ctx, params: GetPurchaseOrderParams) -> ActionResult:
    """Imperal action: get_purchase_order."""
    return await _get_resource(ctx, params, f"/api/order-invoice-status/v1/prod/purchaseorders/{params.order_id}", "id", ["title", "Title", "poNumber"])


@chat.function("list_invoices", "List Invoices, optionally filtered by status.", action_type="read", chain_callable=True, data_model=AribaRecordList, event="sap-ariba-connector.list_invoices")
async def list_invoices(ctx, params: ListInvoicesParams) -> ActionResult:
    """Imperal action: list_invoices."""
    extra = {"status": params.status} if params.status else None
    return await _list_resource(ctx, params, "/api/order-invoice-status/v1/prod/invoices", "id", ["title", "invoiceNumber"], extra)


@chat.function("get_invoice", "Read one Invoice in full by its unique identifier.", action_type="read", chain_callable=True, data_model=AribaRecord, event="sap-ariba-connector.get_invoice")
async def get_invoice(ctx, params: GetInvoiceParams) -> ActionResult:
    """Imperal action: get_invoice."""
    return await _get_resource(ctx, params, f"/api/order-invoice-status/v1/prod/invoices/{params.invoice_id}", "id", ["title", "invoiceNumber"])


@chat.function("list_suppliers", "List Suppliers (Supplier Management), optionally filtered by name.", action_type="read", chain_callable=True, data_model=AribaRecordList, event="sap-ariba-connector.list_suppliers")
async def list_suppliers(ctx, params: ListSuppliersParams) -> ActionResult:
    """Imperal action: list_suppliers."""
    extra = {"name": params.query} if params.query else None
    return await _list_resource(ctx, params, "/api/supplier-information-and-performance-management/v1/prod/suppliers", "id", ["name", "supplierName"], extra)


@chat.function("get_supplier", "Read one Supplier in full by its Ariba Network ID (ANID) or internal identifier.", action_type="read", chain_callable=True, data_model=AribaRecord, event="sap-ariba-connector.get_supplier")
async def get_supplier(ctx, params: GetSupplierParams) -> ActionResult:
    """Imperal action: get_supplier."""
    return await _get_resource(ctx, params, f"/api/supplier-information-and-performance-management/v1/prod/suppliers/{params.supplier_id}", "id", ["name", "supplierName"])


@chat.function("list_sourcing_events", "List Sourcing Events (RFQ/RFP/auction projects), optionally filtered by status.", action_type="read", chain_callable=True, data_model=AribaRecordList, event="sap-ariba-connector.list_sourcing_events")
async def list_sourcing_events(ctx, params: ListSourcingEventsParams) -> ActionResult:
    """Imperal action: list_sourcing_events."""
    extra = {"status": params.status} if params.status else None
    return await _list_resource(ctx, params, "/api/sourcing/v1/prod/events", "id", ["title", "eventName"], extra)


@chat.function("get_sourcing_event", "Read one Sourcing Event in full by its unique identifier.", action_type="read", chain_callable=True, data_model=AribaRecord, event="sap-ariba-connector.get_sourcing_event")
async def get_sourcing_event(ctx, params: GetSourcingEventParams) -> ActionResult:
    """Imperal action: get_sourcing_event."""
    return await _get_resource(ctx, params, f"/api/sourcing/v1/prod/events/{params.event_id}", "id", ["title", "eventName"])


@chat.function("list_contract_workspaces", "List Contract Workspaces, optionally filtered by status.", action_type="read", chain_callable=True, data_model=AribaRecordList, event="sap-ariba-connector.list_contract_workspaces")
async def list_contract_workspaces(ctx, params: ListContractWorkspacesParams) -> ActionResult:
    """Imperal action: list_contract_workspaces."""
    extra = {"status": params.status} if params.status else None
    return await _list_resource(ctx, params, "/api/contract-workspace/v1/prod/workspaces", "id", ["title", "workspaceName"], extra)


@chat.function("get_contract_workspace", "Read one Contract Workspace in full by its unique identifier.", action_type="read", chain_callable=True, data_model=AribaRecord, event="sap-ariba-connector.get_contract_workspace")
async def get_contract_workspace(ctx, params: GetContractWorkspaceParams) -> ActionResult:
    """Imperal action: get_contract_workspace."""
    return await _get_resource(ctx, params, f"/api/contract-workspace/v1/prod/workspaces/{params.workspace_id}", "id", ["title", "workspaceName"])


_AUDIT_TARGETS = [
    ("Requisitions", "/api/requisitioning/v1/prod/requisitions"),
    ("Purchase Orders", "/api/order-invoice-status/v1/prod/purchaseorders"),
    ("Invoices", "/api/order-invoice-status/v1/prod/invoices"),
    ("Suppliers", "/api/supplier-information-and-performance-management/v1/prod/suppliers"),
    ("Sourcing Events", "/api/sourcing/v1/prod/events"),
    ("Contract Workspaces", "/api/contract-workspace/v1/prod/workspaces"),
]


@chat.function("audit_ariba_access", "Probe every core SAP Ariba API package (Requisitions, POs, Invoices, Suppliers, Sourcing Events, Contract Workspaces) and report which are actually licensed for this realm, without changing anything.", action_type="read", chain_callable=True, data_model=AccessAudit, event="sap-ariba-connector.audit_ariba_access")
async def audit_ariba_access(ctx, params: AuditAccessParams) -> ActionResult:
    """Imperal action: audit_ariba_access."""
    connection = await _resolve_connection(ctx, params.connection_id)
    if not connection:
        return await _no_connection_error()
    client = _client_from(connection)
    capabilities: list[Capability] = []
    for name, path in _AUDIT_TARGETS:
        try:
            await client.request("get", path, params={"$top": 1})
            capabilities.append(Capability(name=name, available=True, note="Responded successfully."))
        except ac.SAPAribaError as exc:
            capabilities.append(Capability(name=name, available=False, note=str(exc)))
    return ActionResult.ok(AccessAudit(realm=connection.get("realm", ""), capabilities=capabilities))
