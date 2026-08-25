"""SAP Ariba Connector extension declaration and realm-scoped credential storage.

SAP Ariba API package availability is realm-, license-, and contract-dependent —
Requisitions/POs (Approvable APIs), Suppliers (Supplier Management), Sourcing
Events, and Contract Workspaces are each independently licensed per customer
realm. The connector stores one or more explicitly configured realm connections
and handlers must treat any API package as potentially unavailable until a real
response confirms it.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "sap-ariba-connector",
    version="0.1.0",
    display_name="SAP Ariba",
    description=(
        "Connect your own SAP Ariba realm through OAuth2 client credentials. "
        "Read and safely manage Requisitions, Purchase Orders, Invoices, "
        "Suppliers, Sourcing Events, and Contract Workspaces through the "
        "realm's licensed API packages."
    ),
    icon="icon.svg",
    capabilities=["sap_ariba:read", "sap_ariba:write"],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="sap_ariba",
    description=(
        "SAP Ariba Connector — capability-aware, realm-scoped REST operations "
        "for Requisitions, Purchase Orders, Invoices, Suppliers, Sourcing "
        "Events, and Contract Workspaces, restricted to API packages the "
        "realm has actually licensed."
    ),
)

ext.secret(
    "sap_ariba_connections",
    "JSON list of connected SAP Ariba realms and encrypted OAuth credentials. Managed only through connect_ariba and disconnect_ariba.",
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=90,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one SAP Ariba realm is connected."""
    import json
    raw = await ctx.secrets.get("sap_ariba_connections")
    connections = []
    if raw:
        try:
            connections = json.loads(raw)
        except (TypeError, ValueError):
            connections = []
    return {
        "healthy": bool(connections),
        "detail": f"{len(connections)} SAP Ariba realm(s) connected" if connections else "No SAP Ariba realm connected yet",
    }
