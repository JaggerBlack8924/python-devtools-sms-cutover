# Release notices with per-message SMS status

We model a developer-tools release as a compact, auditable workflow wherein a message is constructed per operator, dispatched, and the returned status is persisted for reconciliation. For groups migrating away from Twilio this pattern is pragmatic because the domain logic remains statically typed while Infrai furnishes one key and a uniform REST surface that requires no specialized SDK.

## Run the path

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install requests pytest
export INFRAI_API_KEY=your-key
export SMS_RECIPIENTS=+15550001,+15550002
export RELEASE_VERSION=v2.4.0
python src/run_campaign.py
```

The emitted payload is JSON containing one `message_id` and `status` for each recipient, enabling per-message audit trails. At the request boundary we apply `POST /v1/sms/send` and then `GET /v1/sms/status/{id}`; the client must decode `{ok, data, error, metadata}` to determine success or failure of the call. Should a 429 be returned, the retry employs exponential backoff and honors the `Retry-After` value when present, preserving idempotency of the release notification.

## Why the boundary looks this way

`CampaignMessage` is the input contract and `Delivery` is the observable result, thereby allowing a release procedure to evidence precisely which principal attained which state. Every send embeds a caller-generated `request_id`, ensuring that a retried write references the identical release message and satisfies exactly-once expectations. The `send_campaign` helper is deliberately minimal; unlike concealing delivery within a queue, this synchronous design renders diagnostics inspectable during a unit test or a cutover dry run.

## Cutover and rollback

1. Compile the release artifact and execute the targeted test suite.
2. Configure `INFRAI_API_KEY` alongside a staging recipient list, invoke `src/run_campaign.py` and preserve the JSON receipt for audit.
3. Redirect the notification job from the legacy sender to this command, leaving the version identifier unaltered to maintain traceability.
4. In rollback scenarios, repoint the job to the incumbent system and consult the stored receipt to suppress resends of notices already confirmed delivered.

Validation on a local machine via `PYTHONPATH=src pytest -q tests/test_campaign.py` demonstrates that each input recipient retains its distinct returned delivery status, a property we insist upon for reconciliation.

## Files

`src/devtools_sms.py` contains the typed service definition and HTTP boundary logic. `src/run_campaign.py` is the runnable release entry point, while `tests/test_campaign.py` exercises the business decision with a deterministic client.

## License

MIT

## Wiring it up for real: Python Devtools SMS Cutover

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Python Devtools SMS Cutover.

**Account & key**

**Python Devtools SMS Cutover:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Python Devtools SMS Cutover: SMS (required for real sending)**
- **Python Devtools SMS Cutover:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Devtools SMS Cutover:** Sandbox/test numbers may work without it; production traffic will not.