"""Thin OAuth2 REST client for SAP Ariba (API Business Hub surface).

Realm capability differs by licensed API package and customer contract. The
client speaks generic REST/JSON and never assumes a package is licensed before
the realm confirms it via a real response.
"""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import urljoin

import httpx

_TOKEN_URL = "https://api.ariba.com/v2/oauth/token"
_API_BASE = "https://openapi.ariba.com"


class SAPAribaError(RuntimeError):
    """A safe provider-facing error; never includes credentials."""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


def rest_items(body: Any) -> list[dict[str, Any]]:
    """Normalise Ariba REST collection envelopes to a list of objects."""
    if isinstance(body, list):
        return [item for item in body if isinstance(item, dict)]
    if not isinstance(body, dict):
        return []
    for key in ("Items", "items", "value", "results"):
        items = body.get(key)
        if isinstance(items, list):
            return items
    return []


class SAPAribaClient:
    """OAuth2 client-credentials REST client for SAP Ariba's realm-scoped API packages."""

    def __init__(
        self,
        realm: str,
        application_key: str,
        application_secret: str,
        api_key: str,
        *,
        timeout: float = 30.0,
    ):
        self.realm = realm.strip()
        self.application_key = application_key
        self.application_secret = application_secret
        self.api_key = api_key
        self.timeout = timeout
        self._token: str | None = None
        self._token_expiry: float = 0.0

    async def _ensure_token(self, http: httpx.AsyncClient) -> None:
        if self._token and time.time() < self._token_expiry - 30:
            return
        resp = await http.post(
            _TOKEN_URL,
            params={"grant_type": "client_credentials"},
            auth=(self.application_key, self.application_secret),
        )
        if resp.status_code >= 400:
            raise SAPAribaError(f"OAuth token request failed ({resp.status_code}).", retryable=resp.status_code >= 500)
        payload = resp.json()
        self._token = payload.get("access_token")
        self._token_expiry = time.time() + float(payload.get("expires_in", 3600))
        if not self._token:
            raise SAPAribaError("OAuth token response did not contain access_token.")

    async def ping(self) -> bool:
        """Verify connectivity and credentials without assuming a specific API package."""
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            await self._ensure_token(http)
            return True

    async def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_body: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            await self._ensure_token(http)
            headers = {
                "Authorization": f"Bearer {self._token}",
                "apiKey": self.api_key,
                "Accept": "application/json",
            }
            merged_params = dict(params or {})
            merged_params["realm"] = self.realm
            url = urljoin(_API_BASE + "/", path.lstrip("/"))
            resp = await http.request(method, url, headers=headers, params=merged_params, json=json_body)
            if resp.status_code == 404:
                raise SAPAribaError(f"API package or resource not found: {path}. It may not be licensed for this realm.")
            if resp.status_code in (401, 403):
                raise SAPAribaError("Not authorized for this operation — check realm authorizations and package licensing.")
            if resp.status_code == 429:
                raise SAPAribaError("Rate limited by SAP Ariba.", retryable=True)
            if resp.status_code >= 500:
                raise SAPAribaError("SAP Ariba returned a server error.", retryable=True)
            if resp.status_code >= 400:
                raise SAPAribaError(f"SAP Ariba rejected the request ({resp.status_code}): {resp.text[:300]}")
            if resp.status_code == 204 or not resp.content:
                return {}
            return resp.json()
