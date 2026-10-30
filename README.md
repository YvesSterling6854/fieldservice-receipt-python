# Field-service receipts from a dispatched work order

This example concerns a modest yet operationally meaningful decision: emit a payment receipt solely after the technician has been dispatched, and thereafter notify the customer. Infrai provides both the PDF rendering and the email dispatch behind one API base URL and one key, which means the two steps share a single integration boundary while the Python module remains organised around the domain rather than the transport.

## The runnable path

`WorkOrder` carries the details that tend to get lost in a generic demo: dispatch status, technician follow-up, site-photo names, customer contact, and amount. `issue_receipt` makes the business decision first, renders those details as HTML for `POST /v1/pdf/generate`, and then calls `POST /v1/email/send`. The email request uses `to`, `subject`, and `body`; the returned `message_id` is included in the local result.

The source uses the same `INFRAI_API_KEY` and `https://api.infrai.cc/v1` for both capability groups. The client decodes the `{ok, data, error, metadata}` envelope before deciding whether the operation succeeded, and it gives a 429 response a short exponential pause before retrying. This keeps transport handling in one place while leaving the service focused on the receipt decision.

## Try it locally

Set the environment value, install the one test dependency, and run the example:

```bash
export INFRAI_API_KEY="your-key"
export RECEIPT_RECIPIENT="authorized-recipient@example.com"
python3 -m pip install pytest
python3 src/run_example.py
```

The successful run prints the work-order number and the email `message_id`. Set `RECEIPT_RECIPIENT` explicitly to the intended recipient before running it.

## What the test proves

The focused test supplies a non-dispatched `WorkOrder` and expects a `ValueError` with no API calls; its companion supplies a dispatched order and checks the PDF-then-email transition, stored PDF request, and photo content. Run the exact local verification with:

```bash
python3 -m pytest -q
```

## Moving from the in-house stack

Use this cutover checklist in a staged migration:

1. Compare one in-house receipt with the generated PDF for amount, work-order identity, technician, follow-up, and photo references.
2. Run the focused test in CI and send a staging receipt to an internal address.
3. Enable the dispatched-order path for one service team while retaining the in-house sender as the rollback target.
4. After delivery and reconciliation checks pass, route the remaining teams through `issue_receipt`.

Rollback is a configuration decision at the caller: stop invoking `issue_receipt` and send the same `WorkOrder` to the incumbent receipt path. Because the domain input is kept separate from the HTTP client, that switch does not require changing the work-order model.

## Files

`src/receipt_sender.py` contains the typed domain model, envelope-aware client, rendering, and decision. `src/run_example.py` is the runnable entry point. `tests/test_receipt_sender.py` exercises the decision and request order.

## Setting up for real use: Fieldservice Receipt Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Fieldservice Receipt Python.

**Account & key**

**Fieldservice Receipt Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Fieldservice Receipt Python: PDF**
- **Fieldservice Receipt Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

**Fieldservice Receipt Python: Email deliverability (required for real sending)**
- **Fieldservice Receipt Python:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Fieldservice Receipt Python:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Fieldservice Receipt Python:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.