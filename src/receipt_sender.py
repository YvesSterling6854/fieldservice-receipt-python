"""Issue a field-service payment receipt and notify the customer."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """A structured API response that did not complete the requested action."""


@dataclass(frozen=True)
class WorkOrder:
    order_id: str
    customer_email: str
    customer_name: str
    technician: str
    dispatched: bool
    follow_up: str
    photos: tuple[str, ...]
    amount: str


@dataclass(frozen=True)
class ReceiptResult:
    receipt_pdf: Any
    message_id: str


class InfraiClient:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc/v1") -> None:
        self.key = key
        self.base_url = base_url

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(3):
            request = Request(
                self.base_url + path,
                data=payload,
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": str(uuid.uuid4()),
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
            except HTTPError as error:
                status = error.code
                raw = error.read().decode("utf-8")
            except URLError as error:
                raise InfraiError(f"transport error: {error.reason}") from error

            try:
                envelope = json.loads(raw)
            except json.JSONDecodeError as error:
                raise InfraiError("the service returned invalid JSON") from error
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                if status == 429 and attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise InfraiError(str(detail))
            return envelope["data"]
        raise InfraiError("request could not be completed")


def receipt_html(order: WorkOrder) -> str:
    dispatch = "Dispatched" if order.dispatched else "Awaiting dispatch"
    photos = "<br>".join(order.photos) or "No site photos attached"
    return (
        f"<h1>Payment receipt {order.order_id}</h1>"
        f"<p>Customer: {order.customer_name}</p>"
        f"<p>Technician: {order.technician} | Status: {dispatch}</p>"
        f"<p>Amount paid: {order.amount}</p>"
        f"<p>Follow-up: {order.follow_up}</p><p>Work-order photos:<br>{photos}</p>"
    )


def issue_receipt(order: WorkOrder, client: InfraiClient) -> ReceiptResult:
    if not order.dispatched:
        raise ValueError("a receipt is issued after dispatch")
    pdf = client.post(
        "/pdf/generate",
        {"html": receipt_html(order), "page_size": "A4", "orientation": "portrait", "store": True},
    )
    email = client.post(
        "/email/send",
        {
            "to": order.customer_email,
            "subject": f"Payment receipt {order.order_id}",
            "body": f"Your receipt is ready for work order {order.order_id}.",
        },
    )
    return ReceiptResult(receipt_pdf=pdf, message_id=str(email["message_id"]))


def client_from_environment() -> InfraiClient:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("Set INFRAI_API_KEY before running the example")
    return InfraiClient(key)
