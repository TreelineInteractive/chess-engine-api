import json
import os
import urllib.error
import urllib.request


def _format_message(record):
    message = json.loads(record["Sns"]["Message"])

    alarm_name = message.get("AlarmName", "unknown")
    new_state = message.get("NewStateValue", "unknown")
    reason = message.get("NewStateReason", "No reason provided.")
    region = message.get("Region", "unknown")
    account = message.get("AWSAccountId", "unknown")
    alarm_arn = message.get("AlarmArn", "")

    color = "#d40e0d" if new_state == "ALARM" else "#2eb886"

    return {
        "text": f"<!channel> App Runner alarm: {alarm_name} is {new_state}",
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"App Runner alarm: {alarm_name}",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*State:*\n{new_state}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Region:*\n{region}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Account:*\n{account}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Alarm ARN:*\n`{alarm_arn}`",
                            },
                        ],
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Reason:*\n{reason}",
                        },
                    },
                ],
            }
        ]
    }


def handler(event, _context):
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]

    for record in event.get("Records", []):
        payload = _format_message(record)
        request = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as response:
                if response.status >= 400:
                    raise RuntimeError(f"Slack webhook returned HTTP {response.status}")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Slack webhook HTTP error: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Slack webhook connection error: {exc.reason}") from exc

    return {"ok": True}
