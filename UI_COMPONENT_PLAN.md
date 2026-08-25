# SAP Ariba Connector — UI component plan

Источники: `Docs/session-notes/UI_COMPONENT_VOCABULARY.md`, `UI_INTERFACE_STANDARD.md`,
`concepts/panels.md`. Основано на функционале `sap-ariba-connector`.

## 0. Разница с IDEAL_ONBOARDING.md
Идеал предполагает живую "лицензионную карту" по каждому API-пакету сразу при
подключении. Текущая реализация показывает это как обычный список через
`audit_ariba_access` (`ui.DataTable`/`ui.List`), без специализированного визуального
"license map" виджета — такого примитива в SDK нет; ближайший существующий
эквивалент — `DataTable` со столбцом-Badge (available/unavailable).

## 1. Компоненты

| Экран | Примитивы | Почему именно эти |
|---|---|---|
| Sidebar (left) | `ui.Stack`(direction="v", align="stretch") + `ui.Text`(realm label) + `ui.Divider` + navigation `ui.ListItem`(Requisitions/Purchase Orders/Invoices/Suppliers/Sourcing Events/Contracts) + `ui.Button`("App settings") | Без карточек по стандарту, без дублирования инструкций из help-диалога. |
| Connect form (sidebar, not connected) | `ui.Form`(action="connect_ariba", submit_label="Verify and connect") + `_field`-labelled `ui.Input`(realm, application key, application secret, API key) + `ui.Button`("How do I get these credentials?" → Dialog) | Форма растянута на всю ширину сайдбара, поля растянуты внутри неё — по UI_INTERFACE_STANDARD. |
| Requisition List (center, `center_overlay=True`) | `ui.Stats`(Total requisitions) + `ui.Input`(param_name="status", placeholder="Например: Approved, Pending Approval...") + `ui.DataTable`(id, title, status Badge, requester, total) | `DataTable` — основной обзор; `Input` для фильтра по статусу. |
| Purchase Order List | `ui.DataTable`(PO number, supplier, status Badge, total, currency) | Тот же паттерн, что requisitions — единообразие. |
| Invoice List | `ui.DataTable`(invoice number, supplier, status Badge, amount, due date) | AP-аналитику нужен статус и сумма на одном экране. |
| Supplier List | `ui.DataTable`(name, ANID, qualification status Badge, category) | ANID — уникальный идентификатор в Ariba Network, обязателен к показу. |
| Sourcing Event List | `ui.DataTable`(event id, title, status Badge, close date) | Category manager должен видеть открытые события и дедлайны сразу. |
| Contract Workspace List | `ui.DataTable`(workspace id, title, status Badge, owner) | Тот же единообразный паттерн. |
| Access audit result | `ui.DataTable`(API package, availability Badge, note) | `audit_ariba_access` — единственный экран, где Badge реально нужен для honesty gate. |
| App settings (center, `center_overlay=True`) | `ui.Stack` per connection: realm label + auth mode + `ui.Button`("Disconnect", variant="danger") | Единственное место для disconnect — не дублируется в sidebar. |
| Help dialog | `ui.Dialog` с шагами получения OAuth app key/secret + API key на developer.ariba.com | Единственное место с setup-инструкциями — не дублируется в sidebar/форме. |

## 2. Соответствие функциям
`connect_ariba`, `disconnect_ariba`, `list_connections` → форма + settings панель.
`list_requisitions`/`get_requisition`/`create_requisition` → Requisition List/Detail.
`list_purchase_orders`/`get_purchase_order` → PO List/Detail.
`list_invoices`/`get_invoice` → Invoice List/Detail.
`list_suppliers`/`get_supplier` → Supplier List/Detail.
`list_sourcing_events`/`get_sourcing_event` → Sourcing Event List/Detail.
`list_contract_workspaces`/`get_contract_workspace` → Contract List/Detail.
`audit_ariba_access` → отдельный экран с DataTable-картой лицензий.
