# SAP Ariba — Connector Discovery

**Discovery date:** 2026-08-25
**Release scope:** Tier 1 + Tier 2 (maximum coverage available without cXML/EDI
punchout infrastructure), per standing instruction ("максимальный функционал,
полный максимум" applied to every new app).
**Decision owner:** Vlad — Procurement category build-out.

## 1. Target service and official sources

SAP Ariba has **no single unified API** — it exposes a family of REST APIs through
the **SAP Ariba Developer Portal / SAP API Business Hub** (developer.ariba.com,
api.sap.com/package/AribaProcurement), grouped by functional module. Each module is
independently licensed and independently provisioned per customer "realm" (the
Ariba site/tenant identifier, e.g. `AN01000000042-T`).

### Official sources referenced
- SAP Ariba Developer Portal: <https://developer.ariba.com/api/>
- SAP API Business Hub, Ariba package catalog: <https://api.sap.com/package/AribaProcurement>
- SAP Ariba OAuth2 authentication guide: <https://developer.ariba.com/api/authentication/>
- SAP Ariba Approvable APIs (Requisition, PO, Invoice read/write): <https://developer.ariba.com/api/approvable-apis/>
- SAP Ariba Supplier Management APIs: <https://developer.ariba.com/api/supplier-management-apis/>
- SAP Ariba Contract Workspace APIs: <https://developer.ariba.com/api/contract-management-apis/>
- SAP Ariba Sourcing APIs (Event/Project): <https://developer.ariba.com/api/sourcing-apis/>

(Exact per-endpoint paths re-verified against the live Developer Portal catalog at
implementation time — SAP restructures API package names/versions across releases;
every resource is treated as potentially unlicensed/unprovisioned for a given realm
until a real call confirms it, same honesty gate as every other Oracle/SAP connector
in this portfolio.)

## 2. Auth model — OAuth2 client credentials, realm-scoped

SAP Ariba APIs authenticate via **OAuth2 Client Credentials** against SAP API
Business Hub's shared token endpoint (`api.token.ariba.com` family), returning a
Bearer token. Every API call additionally requires:
- `apiKey` header (issued per registered application in the SAP Ariba Developer
  Portal) — a *separate* credential from the OAuth client id/secret.
- Realm scoping — most endpoints require identifying the target Ariba site/realm
  either via query parameter (`realm=<customer-realm>`) or a resource-specific
  path segment, because one OAuth application can be authorized against multiple
  customer realms.

This connector models `connect_ariba` with four fields: `client_id`, `client_secret`,
`api_key`, `realm` — mirroring the SAP S/4HANA / SAP SuccessFactors connectors'
`connect_*` shape (label + explicit credential fields, OAuth2-only since Ariba does
not offer a Basic Auth REST fallback like S/4HANA Gateway does).

## 3. API surfaces in scope (Tier 1 — core Source-to-Pay objects)

| Domain | API family | Resource | Capability |
|---|---|---|---|
| Procurement/Buying | Approvable APIs | Requisition | list/get purchase requisitions |
| Procurement/Buying | Approvable APIs | Purchase Order | list/get/create purchase orders |
| Procurement/Buying | Approvable APIs | Invoice | list/get supplier invoices |
| Supplier Management | Supplier Management APIs | Supplier | list/get supplier profiles + status |
| Sourcing | Sourcing APIs | Sourcing Event/Project | list/get sourcing events (RFx/auction) |
| Contracts | Contract Management APIs | Contract Workspace | list/get contract workspaces |

Tier 2 (deferred to a later pass, explicitly out of v1 scope): **cXML-based Ariba
Network punchout/order/invoice transactions** — these run over a separate B2B
messaging channel (cXML over HTTPS, not the REST Approvable APIs), require a
registered Ariba Network trading-relationship and message routing setup that is
inherently per-customer infrastructure, not a stable versioned REST surface a
generic connector can safely target without that setup already existing. Recorded
here explicitly rather than silently dropped, per the task's requirement to decide
and record the cXML scope call.

## 4. Terminology notes (Ariba-specific, must NOT be renamed to generic terms)
- **Realm** — the customer's Ariba site/tenant identifier; not "tenant" or "org" in
  API parameters, though "tenant" is used informally in UI copy for user clarity.
- **Requisition** vs **Purchase Order** vs **Invoice** — distinct Approvable
  document types, each with its own approval workflow status.
- **Sourcing Event** (RFx / auction / RFP) vs **Sourcing Project** — an Event is a
  single bidding round; a Project can contain multiple Events.
- **Contract Workspace** — Ariba's contract lifecycle container (not just a
  document); has its own status/workflow separate from the underlying document.
- **Supplier** (not "Vendor") — Ariba's Supplier Management vocabulary.

## 5. Known constraints / honesty gates
- Every realm enables a different subset of licensed API packages — the client
  must attempt the real call and surface Ariba's actual error/status rather than
  assume a package is licensed, exactly like the Oracle Fusion/SuccessFactors
  connectors' approach.
- Ariba's REST APIs paginate via `$top`/`$skip` or a `pageToken`, endpoint-
  dependent — the client normalises both patterns rather than assuming one.
- No credentials, sandbox realm, or live Ariba system are available to this build
  process — every endpoint path/field name is taken from SAP's published Developer
  Portal API reference, not guessed from memory.
- Rate limits are enforced per apiKey by SAP API Business Hub infrastructure and are
  contract-dependent; the client surfaces HTTP 429 as a retryable error rather than
  silently retrying with an assumed backoff schedule.
