"""SAP Ariba Connector panel UI, aligned with UI_INTERFACE_STANDARD.md.

The left sidebar contains plain stacked content only: no card containers, all
form controls have visible labels with contextual placeholders, and App
settings is the last element. Setup instructions live solely in the help
dialog and are not duplicated in the form/sidebar. The connect form stretches
to the full width of the sidebar and its fields stretch to the form's width.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers as h


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", icon="settings", on_click=ui.Call("__panel__sap_ariba_settings"),
    )


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="caption"), node,
    ])


def _connection_rows(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Text("No SAP Ariba realms connected yet.", variant="caption")
    children: list[ui.UINode] = []
    for index, connection in enumerate(connections):
        if index:
            children.append(ui.Divider())
        label = connection.get("label") or connection.get("realm", "")
        children.append(ui.Stack(direction="v", gap=1, align="start", children=[
            ui.Text(label, variant="body"),
            ui.Text(f"Realm: {connection.get('realm', '')}", variant="caption"),
        ]))
    return ui.Stack(direction="v", gap=2, align="stretch", children=children)


def _connect_form() -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Button("How do I set this up?", variant="ghost", size="sm", icon="HelpCircle",
                  on_click=ui.Call("__panel__sap_ariba_connect_help")),
        ui.Form(action="connect_ariba", submit_label="Verify and connect", children=[
            _field("Realm label (optional)", ui.Input(param_name="label", placeholder="e.g. Acme production realm")),
            _field("Ariba realm/site ID", ui.Input(param_name="realm", placeholder="e.g. AN01000000042-T")),
            _field("OAuth application key", ui.Input(param_name="application_key", placeholder="Application key from SAP Ariba Developer Portal")),
            _field("OAuth application secret", ui.Password(param_name="application_secret", placeholder="Secret for that application key")),
            _field("SAP API Business Hub API key", ui.Password(param_name="api_key", placeholder="apikey header value for your subscribed Ariba packages")),
        ]),
    ])


@ext.panel("sap_ariba_connect_help", slot="center", title="Connect SAP Ariba", center_overlay=True)
async def sap_ariba_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Find your realm ID in Ariba under System Realm Information (Manage > Site Manager, or ask your Ariba administrator) — it looks like AN01000000042-T.", variant="body"),
        ui.Text("Create an OAuth application (application key + secret) and subscribe to the Ariba API packages you need (Requisitioning, Procurement, Supplier Management, Sourcing, Contracts) via the SAP Ariba Developer Portal (developer.ariba.com), then generate an API Business Hub apikey for those packages.", variant="body"),
        ui.Alert(title="Realm-specific licensing", message="Each API package (Requisitions, Purchase Orders, Suppliers, Sourcing Events, Contract Workspaces) is independently licensed per realm. After connecting, run the access audit to see exactly which packages are enabled for this realm. cXML punchout/order/invoice transactions are not covered by this connector.", type="warning"),
    ])


@ext.panel("sap_ariba_sidebar", slot="left", title="SAP Ariba", default_width=340, min_width=280, max_width=460)
async def sap_ariba_sidebar(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    body: list[ui.UINode] = [ui.Text("SAP Ariba", variant="title")]
    if connections:
        body.append(_connection_rows(connections))
        body.append(ui.Divider())
        body.append(ui.ListItem(title="Overview", icon="LayoutDashboard",
                                 on_click=ui.Call("__panel__sap_ariba_center")))
        for label, key in [
            ("Requisitions", "requisitions"), ("Purchase Orders", "purchase_orders"),
            ("Invoices", "invoices"), ("Suppliers", "suppliers"),
            ("Sourcing Events", "sourcing_events"), ("Contract Workspaces", "contract_workspaces"),
        ]:
            body.append(ui.ListItem(title=label, icon="ChevronRight",
                                     on_click=ui.Call("__panel__sap_ariba_center", {"section": key})))
    else:
        body.append(_connect_form())
    body.append(ui.Divider())
    body.append(_settings_button())
    return ui.Stack(direction="v", gap=3, align="stretch", children=body)


@ext.panel("sap_ariba_center", slot="center", title="SAP Ariba overview", icon="ShoppingCart", center_overlay=True)
async def sap_ariba_center_panel(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Connect a SAP Ariba realm from the sidebar to see it here.", icon="🟦")

    from schemas import (
        AuditAccessParams, ListRequisitionsParams, ListPurchaseOrdersParams,
        ListInvoicesParams, ListSuppliersParams, ListSourcingEventsParams,
        ListContractWorkspacesParams,
    )

    conn_id = connections[0].get("id", "")
    section = kwargs.get("section", "")
    body: list[ui.UINode] = []

    async def _section_table(title: str, result, columns) -> None:
        body.append(ui.Text(title, variant="subtitle"))
        if result.success and result.data and result.data.items:
            rows = [{"id": r.id, "title": r.title} for r in result.data.items]
            body.append(ui.DataTable(columns=columns, rows=rows))
        else:
            body.append(ui.Empty(message=f"No {title.lower()} found, or this package isn't licensed for this realm.", icon="Inbox"))

    if not section:
        body.append(ui.Text("Access audit", variant="subtitle"))
        audit_result = await h.audit_ariba_access(ctx, AuditAccessParams(connection_id=conn_id))
        if audit_result.success and audit_result.data:
            r = audit_result.data
            body.append(ui.Stats(children=[
                ui.Stat(label="Available", value=str(r.available_count)),
                ui.Stat(label="Unavailable", value=str(r.unavailable_count)),
            ]))
            for c in r.checks:
                color = "green" if c.available else "red"
                body.append(ui.Stack(direction="h", gap=2, align="center", children=[
                    ui.Badge(label="OK" if c.available else "BLOCKED", color=color),
                    ui.Text(c.name, variant="body"),
                ]))
        else:
            body.append(ui.Text("Could not run the access audit.", variant="caption"))
    elif section == "requisitions":
        result = await h.list_requisitions(ctx, ListRequisitionsParams(connection_id=conn_id, top=25))
        await _section_table("Requisitions", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Title"}])
    elif section == "purchase_orders":
        result = await h.list_purchase_orders(ctx, ListPurchaseOrdersParams(connection_id=conn_id, top=25))
        await _section_table("Purchase Orders", result, [{"key": "id", "label": "PO"}, {"key": "title", "label": "Title"}])
    elif section == "invoices":
        result = await h.list_invoices(ctx, ListInvoicesParams(connection_id=conn_id, top=25))
        await _section_table("Invoices", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Title"}])
    elif section == "suppliers":
        result = await h.list_suppliers(ctx, ListSuppliersParams(connection_id=conn_id, top=25))
        await _section_table("Suppliers", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Name"}])
    elif section == "sourcing_events":
        result = await h.list_sourcing_events(ctx, ListSourcingEventsParams(connection_id=conn_id, top=25))
        await _section_table("Sourcing Events", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Title"}])
    elif section == "contract_workspaces":
        result = await h.list_contract_workspaces(ctx, ListContractWorkspacesParams(connection_id=conn_id, top=25))
        await _section_table("Contract Workspaces", result, [{"key": "id", "label": "ID"}, {"key": "title", "label": "Title"}])

    return ui.Stack(direction="v", gap=3, align="stretch", children=body)
