from devtools_sms import CampaignMessage, Delivery, send_campaign


class FakeClient:
    def sms_send(self, to, message, request_id):
        return {"message_id": "m-" + request_id}

    def sms_status(self, message_id):
        return {"status": "delivered"}


def test_campaign_keeps_per_message_delivery_status():
    messages = [CampaignMessage("+15550001", "release", "r-1"), CampaignMessage("+15550002", "release", "r-2")]
    assert send_campaign(messages, FakeClient()) == [
        Delivery("+15550001", "m-r-1", "delivered"),
        Delivery("+15550002", "m-r-2", "delivered"),
    ]

