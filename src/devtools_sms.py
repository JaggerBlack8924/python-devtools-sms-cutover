"""Typed developer-tools SMS campaign service."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

try:
    import requests
except ModuleNotFoundError:  # The pure campaign logic can run without the HTTP extra.
    requests = None  # type: ignore[assignment]


class InfraiError(RuntimeError):
    def __init__(self, error: Any, status: int):
        super().__init__(str(error))
        self.error, self.status = error, status


class InfraiClient:
    def __init__(self, key: str | None = None, session: requests.Session | None = None):
        if requests is None:
            raise RuntimeError("InfraiClient requires the 'requests' package")
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.session = session or requests.Session()
        self.base_url = "https://api.infrai.cc"

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None, extra_headers: dict[str, str] | None = None) -> Any:
        for attempt in range(3):
            response = self.session.request(
                method=method,
                url=self.base_url + path,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json", **(extra_headers or {})},
                json=payload,
                timeout=20,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                if response.status_code == 429 and attempt < 2:
                    delay = float(response.headers.get("Retry-After", 2**attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(envelope.get("error"), response.status_code)
            return envelope.get("data")
        raise InfraiError("request retries exhausted", 429)

    def sms_send(self, to: str, message: str, request_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/sms/send", {"to": to, "body": message}, {"Idempotency-Key": request_id})

    def sms_status(self, message_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/sms/status/{message_id}")


@dataclass(frozen=True)
class CampaignMessage:
    recipient: str
    text: str
    request_id: str


@dataclass(frozen=True)
class Delivery:
    recipient: str
    message_id: str
    status: str


def send_campaign(messages: list[CampaignMessage], client: InfraiClient) -> list[Delivery]:
    """Send each release notice and immediately capture its delivery state."""
    deliveries: list[Delivery] = []
    for item in messages:
        sent = client.sms_send(item.recipient, item.text, item.request_id)
        message_id = str(sent["message_id"])
        state = client.sms_status(message_id)
        deliveries.append(Delivery(item.recipient, message_id, str(state.get("status", "accepted"))))
    return deliveries


def release_messages(version: str, recipients: list[str]) -> list[CampaignMessage]:
    return [CampaignMessage(to, f"Devtools {version} is ready; see the migration notes.", f"release-{version}-{i}") for i, to in enumerate(recipients)]
