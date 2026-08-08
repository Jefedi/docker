> ## Documentation Index
> Fetch the complete documentation index at: https://docs.pangolin.net/llms.txt
> Use this file to discover all available pages before exploring further.

# Event Streaming

> Stream Pangolin log events to external collectors and SIEM tools

<div />

Log streaming forwards your organization's audit logs to external data collectors such as Datadog, Splunk, Microsoft Sentinel, Elastic, or any HTTP endpoint you operate. You add a **destination** (how events are delivered), choose which **log types** to include, and Pangolin pushes new events as they are recorded.

<Note>
  Event streaming is only available in [Pangolin Cloud](https://app.pangolin.net/auth/signup) or self-hosted [Enterprise Edition](/self-host/enterprise-edition).
</Note>

## In the dashboard

Open **Organization → Logs & Analytics → Streaming** to add destinations and monitor delivery status. Each destination has its own connection settings, optional body customization (where supported), and log-type selection.

## Log types

You choose which categories each destination receives. Only log types enabled for your organization can be streamed.

<Frame>
  <img src="https://mintcdn.com/fossorial/HS4HJAePwGJVJiz3/images/streaming-log-types.png?fit=max&auto=format&n=HS4HJAePwGJVJiz3&q=85&s=3e93d61cf32574caeffdfbf727953f9f" alt="Log type selection for a streaming destination" centered width="3456" height="1992" data-path="images/streaming-log-types.png" />
</Frame>

## Destination types

Each destination type has its own configuration and payload behavior. Select **Add destination** and pick a delivery method.

<Frame>
  <img src="https://mintcdn.com/fossorial/MhTcSrnIhCWA52yp/images/streaming-add-destination.png?fit=max&auto=format&n=MhTcSrnIhCWA52yp&q=85&s=b6ab8574d34346eafe7fd813b0034575" alt="Add destination dialog in the Pangolin dashboard" centered width="3456" height="1992" data-path="images/streaming-add-destination.png" />
</Frame>

<CardGroup cols={2}>
  <Card title="HTTP webhook" icon="globe" href="/manage/analytics/streaming/http">
    POST JSON or NDJSON to any URL. Supports custom body templates, authentication, and payload formats for SIEMs and generic webhooks.
  </Card>

  <Card title="Amazon S3" icon="bucket" href="/manage/analytics/streaming/s3">
    Upload batched audit logs to S3 or S3-compatible storage. JSON array, NDJSON, or CSV with optional gzip.
  </Card>
</CardGroup>

### Other destinations

Amazon S3 and HTTP webhooks are documented above. For Datadog, Microsoft Sentinel, or other vendor-specific setups, contact [sales@pangolin.net](mailto:sales@pangolin.net).

* **No backfill:** New destinations start from the current log cursor. Historical logs already in Pangolin are not replayed.
* **Per-log-type cursors:** Each enabled log type on a destination is tracked independently.
* **Errors in the UI:** When delivery fails, the destination's last error is shown in the dashboard so you can fix configuration or endpoint issues.
