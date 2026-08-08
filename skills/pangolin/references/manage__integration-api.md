> ## Documentation Index
> Fetch the complete documentation index at: https://docs.pangolin.net/llms.txt
> Use this file to discover all available pages before exploring further.

# Integration API

> Learn how to use Pangolin's REST API to automate and script operations with fine-grained permissions

<div />

<Warning>
  Pangolin is in heavy development. The REST API routes and behavior may include breaking changes between updates. We will do our best to document large changes.
</Warning>

The API is REST-based and supports many operations available through the web interface. Authentication uses Bearer tokens, and you can create multiple API keys with specific permissions for different use cases.

For self-hosted editions, the integration API must be enabled. Check out [the documentation](/self-host/advanced/integration-api) for how to enable the integration API.

## Authentication

All API requests require authentication using a Bearer token in the Authorization header:

<CodeGroup>
  ```bash cURL theme={"theme":"gruvbox-light-hard"}
  curl -H "Authorization: Bearer YOUR_API_KEY" \
    https://api.example.com/v1/
  ```

  ```javascript JavaScript theme={"theme":"gruvbox-light-hard"}
  const response = await fetch('https://api.example.com/v1/endpoint', {
    headers: {
      'Authorization': `Bearer ${apiKey}`
    }
  });
  ```

  ```python Python theme={"theme":"gruvbox-light-hard"}
  import requests

  headers = {'Authorization': f'Bearer {api_key}'}
  response = requests.get('https://api.example.com/v1/endpoint', headers=headers)
  ```
</CodeGroup>

## API Key Types

Pangolin supports two types of API keys with different permission levels:

### Organization API Keys

Organization API keys are created by organization admins and have limited scope to perform actions only in that organization.

### Root API Keys

Root API keys have some extra permissions and can execute operations across orgs. They are only available in the fully self-hosted editions of Pangolin:

<Warning>
  Root API keys have elevated permissions and should be used carefully. Only create them when you need server-wide access.
</Warning>

## Creating API Keys

<Steps>
  <Step title="Access the admin panel">
    Navigate to your admin panel:

    * **Organization keys**: Organization → API Keys
    * **Root keys**: Server Admin → API Keys (self-hosted only)
  </Step>

  <Step title="Generate a new key">
    Click "Create API Key" and provide a descriptive name for the key.
  </Step>

  <Step title="Configure permissions">
    Select the specific permissions your API key needs from the permissions selector.

    <Frame caption="API key permissions selector showing available operations">
      <img src="https://mintcdn.com/fossorial/u-2SUNWyK_LJL3sU/images/permissions.png?fit=max&auto=format&n=u-2SUNWyK_LJL3sU&q=85&s=9d509a7ab8a4286075e9b21af621d8e4" alt="API Key Permissions" width="3042" height="1624" data-path="images/permissions.png" />
    </Frame>
  </Step>

  <Step title="Copy and secure your key">
    Copy the generated API key immediately. It won't be shown again.

    <Warning>
      Store API keys securely and never commit them to version control. Use environment variables or secure secret management.
    </Warning>
  </Step>
</Steps>

## API Documentation

For a minimal walkthrough of common flows (sites, resources, targets, assigning roles and users), see [Common API Routes](/manage/common-api-routes).

View the full Swagger docs here: [https://api.pangolin.net/v1/docs](https://api.pangolin.net/v1/docs).

Interactive API documentation is available through Swagger UI:

<Frame caption="Swagger UI showing API endpoints and interactive testing">
  <img src="https://mintcdn.com/fossorial/u-2SUNWyK_LJL3sU/images/swagger.png?fit=max&auto=format&n=u-2SUNWyK_LJL3sU&q=85&s=a64ee1f3a7c40bf4f2bd19fe3cc16de9" alt="Swagger Docs" width="4556" height="2692" data-path="images/swagger.png" />
</Frame>

For self-hosted Pangolin, access the documentation at `https://api.your-domain.com/v1/docs`.
