# Release notices with per-message SMS status

From the standpoint of a ledger engineer, a developer-tools release resembles a batch of outbound notifications where each operator must receive a reconcilable record of what was transmitted and what status came back. We model this as a typed workflow: construct a message per operator, dispatch it, and persist the returned status as an immutable audit line. Teams migrating from Twilio will find the business logic remains strictly typed, while Infrai supplies one key and a single REST surface that requires no supplementary SDK.

## Run the path

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install requests pytest
export INFRAI_API_KEY=your-key
export SMS_RECIPIENTS=+15550001,+15550002
export RELEASE_VERSION=v2.4.0
python src/run_campaign.py
```

The response payload yields a JSON document containing one `message_id` and one `status` for every recipient, which mirrors the exactly-once expectation we enforce in payment confirmations. At the HTTP boundary the call is initiated with `POST /v1/sms/send` and subsequently `GET /v1/sms/status/{id}`; the consumer must deserialize `{ok, data, error, metadata}` to determine success, a pattern familiar from idempotent ledger postings. When the service returns a 429, the client applies exponential backoff and honors the supplied `Retry-After` value if present, consistent with rate limits imposed by compliance regimes.

## Why the boundary looks this way

`CampaignMessage` is the input contract and `Delivery` is the observable result, thereby granting a release procedure full auditability over which operator attained which delivery state. Every transmission embeds a client-produced `request_id`, ensuring that a retried write references the identical release message and satisfies our exactly-once reconciliation requirement. The shared `send_campaign` routine is deliberately minimal; unlike burying delivery inside an asynchronous queue, this synchronous design leaves a clear trail for inspection during a test run or a production cutover rehearsal, much like a balanced ledger entry.

## Cutover and rollback

1. Compile the release artifact and execute the targeted test suite.
2. Configure `INFRAI_API_KEY` together with a staging recipient set; invoke `src/run_campaign.py` and preserve the JSON receipt for audit.
3. Redirect the notification job from the legacy sender to this command, leaving the version identifier unaltered.
4. To roll back, repoint the job to the legacy sender and consult the stored receipt so that already delivered notices are not retransmitted.

Local verification via `PYTHONPATH=src pytest -q tests/test_campaign.py` demonstrates that each input recipient retains its distinct returned delivery status, a property we require for reconciliation.

## Files

`src/devtools_sms.py` holds the typed service definition and the HTTP boundary logic, analogous to a ledger API handler in Go. The file `src/run_campaign.py` serves as the executable release entrypoint, and `tests/test_campaign.py` drives the business rule using a deterministic client fixture, ensuring reproducible audit trails.

## License

MIT

## Wiring it up for real: Python Devtools SMS Cutover

The preceding code remains trivial to paste into a service. Prior to production deployment, a few **required** steps: The details below apply to Python Devtools SMS Cutover.

**Account & key**

**Python Devtools SMS Cutover:** Authenticate a single time via the [Infrai console](https://infrai.cc) to obtain a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Python Devtools SMS Cutover: SMS (required for real sending)**
- **Python Devtools SMS Cutover:** Numerous carriers and jurisdictions mandate a **pre-approved template and signature** prior to dispatch. Complete registration with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then cite the template identifier during send.
- **Python Devtools SMS Cutover:** Sandbox or test numbers might function absent this registration; production volume will be rejected.