"""SAP Ariba Connector App settings center panel.

Connection setup guidance lives exclusively in sap_ariba_connect_help.
This panel contains current connection state and destructive disconnect actions only.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers as h


def _connection_row(connection: dict) -> ui.UINode:
    label = connection.get("label") or connection.get("realm", "")
    return ui.Stack(direction="v", gap=1, align="start", children=[
        ui.Text(label, variant="body"),
        ui.Text(f"Realm: {connection.get('realm', '')}", variant="caption"),
        ui.Button(
            "Disconnect", variant="danger", size="sm",
            on_click=ui.Call("disconnect_ariba", {"connection_id": connection.get("id", "")}),
        ),
    ])


@ext.panel("sap_ariba_settings", slot="center", title="SAP Ariba settings", icon="settings", center_overlay=True)
async def sap_ariba_settings_panel(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", gap=2, align="start", children=[
            ui.Header(text="App settings", level=2, subtitle="Manage saved SAP Ariba realms"),
            ui.Text("No SAP Ariba realms are connected yet.", variant="caption"),
        ])
    rows: list[ui.UINode] = [
        ui.Header(text="App settings", level=2, subtitle="Manage saved SAP Ariba realms"),
        ui.Text("Connections", variant="subtitle"),
    ]
    for index, connection in enumerate(connections):
        if index:
            rows.append(ui.Divider())
        rows.append(_connection_row(connection))
    return ui.Stack(direction="v", gap=3, align="stretch", children=rows)
