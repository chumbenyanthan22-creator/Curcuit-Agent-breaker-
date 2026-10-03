# Slack loop alerts

Set `SLACK_WEBHOOK_URL` in the backend environment. The `SupabaseLogger` accepts a `SlackAlerter` and schedules the Block Kit POST on a daemon thread so detector enforcement never waits on Slack.

## Local run

```sh
python examples/slack_demo.py
uvicorn slack_webhook_handler:app --host 0.0.0.0 --port 8000
```

Configure the Slack app’s Interactivity Request URL as:

```text
https://<backend-origin>/webhook/slack
```

The Continue button resets the registered detector session. Kill calls `pause_session` and keeps the session paused.

## Deployment

The repository includes `api/webhook/slack.py` for Vercel’s Python runtime and a `Procfile` for Railway or any Procfile-compatible host. The current Vercel project was originally configured as a static frontend; deployment of the Python function requires enabling/authorizing the Vercel connector or connecting the repository in Vercel.

The in-memory session registry is suitable for the proof/demo. A production multi-instance deployment should persist Continue/Kill control state in Supabase or use a durable backend so a Slack callback can reach the correct detector process.
