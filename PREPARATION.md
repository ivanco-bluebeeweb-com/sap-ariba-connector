# SAP Ariba Connector — Preparation

**Version:** 0.1.0 (planning)
**Date:** 2026-08-25
**Product owner:** Vlad / Bluebeeweb
**Related delivery task:** BBW Imperal Apps #2578 — `[App Development] SAP Ariba Connector`
**Scope decision:** maximum feasible capability through the realm's licensed API
packages (per standing "максимальный функционал" instruction).

## 1. App passport

**Name:** SAP Ariba Connector
**One-line purpose:** Connect an organization's own SAP Ariba realm to read and
safely manage the Source-to-Pay cycle — Requisitions, Purchase Orders, Invoices,
Suppliers, Sourcing Events, and Contract Workspaces — through SAP's official REST
API Business Hub surface.

**Why now:** SAP Ariba is the dominant Procurement/Source-to-Pay platform and
Ariba Network trading partner backbone. Procurement and AP teams need plain-
language access to purchasing/supplier/contract data without navigating Ariba's
own dense UI or waiting on integration teams for point-to-point cXML feeds.

**What it is not:**
- Not a replacement for Ariba's own approval workflows or Ariba Network trading
  partner setup.
- Does not implement cXML punchout/order/invoice transactions (see
  `CONNECTOR_DISCOVERY.md` §3 — explicitly deferred, separate B2B messaging
  infrastructure, not a stable generic REST surface).
- Does not assume any API package is licensed for a given realm — every call
  treats the resource as potentially unavailable until a real response confirms it.

## 2. Human problem

> A procurement officer, AP analyst, or category manager needs to check a
> requisition's approval status, look up a purchase order, review a supplier's
> qualification status, or see which sourcing events are still open — without
> hunting through Ariba's own multi-module UI.

### Personas and high-value moments
| Persona | Trigger | Value |
|---|---|---|
| Procurement officer | Needs requisition/PO status | Track approvals in plain language |
| AP/invoice analyst | Needs invoice status | See matched/unmatched/paid invoices |
| Category manager | Needs sourcing event status | Track RFx/auction progress |
| Supplier manager | Needs supplier qualification status | See onboarding/compliance state |
| Contract manager | Needs contract workspace status | Track CLM lifecycle stage |
| Procurement admin | Needs to audit connector reach | See which API packages are actually licensed |

## 3. Release scope (Tier 1/2)
See `CONNECTOR_DISCOVERY.md` §3 for the resource table. Tier 1 = Requisitions,
Purchase Orders, Invoices (read + PO create), Suppliers, Sourcing Events, Contract
Workspaces (read). Tier 2 (deferred) = cXML Ariba Network punchout/order/invoice
transactions — recorded as an explicit non-goal for v1, not silently dropped.

## 4. Non-goals
- No cXML/EDI punchout integration in v1 (see above).
- No duplication of SAP S/4HANA Connector's financial posting/journal-entry scope
  — Ariba owns the pre-financial Source-to-Pay cycle up to invoice approval; the
  actual GL posting is an S/4HANA/ERP-side concern already covered by the SAP
  S/4HANA Connector and Oracle Fusion ERP Connector.

## 5. Cross-reference
UX map, first-launch flow: see `IDEAL_ONBOARDING.md` and `UI_COMPONENT_PLAN.md`
(both required before `panels.py`, per `ONBOARDING_FIRST_LAUNCH_STANDARD.md`).
