import pytest

from src.receipt_sender import InfraiClient, WorkOrder, issue_receipt


class RecordingClient(InfraiClient):
    def __init__(self) -> None:
        super().__init__("test-key")
        self.calls = []

    def post(self, path, body):
        self.calls.append((path, body))
        if path == "/pdf/generate":
            return {"id": "receipt-1"}
        return {"message_id": "message-1"}


def test_receipt_requires_dispatch_before_pdf_and_email() -> None:
    order = WorkOrder("WO-1", "a@example.com", "A", "T", False, "Call back", (), "10 USD")
    with pytest.raises(ValueError, match="after dispatch"):
        issue_receipt(order, RecordingClient())


def test_dispatched_order_generates_pdf_then_sends_email() -> None:
    client = RecordingClient()
    order = WorkOrder("WO-2", "a@example.com", "A", "T", True, "Call back", ("photo.jpg",), "10 USD")
    result = issue_receipt(order, client)
    assert result.message_id == "message-1"
    assert [path for path, _ in client.calls] == ["/pdf/generate", "/email/send"]
    assert client.calls[0][1]["store"] is True
    assert "photo.jpg" in client.calls[0][1]["html"]
