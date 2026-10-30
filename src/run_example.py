import os

from receipt_sender import WorkOrder, client_from_environment, issue_receipt


def main() -> None:
    recipient = os.environ.get("RECEIPT_RECIPIENT")
    if not recipient:
        raise RuntimeError("Set RECEIPT_RECIPIENT before running the example")
    order = WorkOrder(
        order_id="WO-1042",
        customer_email=recipient,
        customer_name="Mina Chen",
        technician="Jordan Lee",
        dispatched=True,
        follow_up="Return visit scheduled for Friday",
        photos=("arrival.jpg", "completed-work.jpg"),
        amount="248.00 USD",
    )
    result = issue_receipt(order, client_from_environment())
    print(f"Receipt issued for {order.order_id}; email message_id={result.message_id}")


if __name__ == "__main__":
    main()
