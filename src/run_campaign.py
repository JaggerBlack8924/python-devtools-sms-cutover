import json
import os

from devtools_sms import InfraiClient, release_messages, send_campaign


def main() -> None:
    recipients = [value.strip() for value in os.environ.get("SMS_RECIPIENTS", "").split(",") if value.strip()]
    if not recipients:
        raise SystemExit("Set SMS_RECIPIENTS to comma-separated phone numbers")
    deliveries = send_campaign(release_messages(os.environ.get("RELEASE_VERSION", "v2"), recipients), InfraiClient())
    print(json.dumps([delivery.__dict__ for delivery in deliveries], indent=2))


if __name__ == "__main__":
    main()

