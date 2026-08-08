> ## Documentation Index
> Fetch the complete documentation index at: https://docs.pangolin.net/llms.txt
> Use this file to discover all available pages before exploring further.

# OAuth2/OIDC

> Configure OpenID Connect identity provider for external authentication

<div />

This identity provider follows the OpenID Connect protocol. This means that it can be used to connect to any external identity provider that supports the OpenID Connect protocol such as Authentik, Keycloak, Okta, etc.

## Creating a Generic OAuth2/OIDC IdP in Pangolin

In Pangolin, go to "Identity Providers" and click "Add Identity Provider". Select the OAuth2/OIDC provider option.

<Frame>
  <img src="https://mintcdn.com/fossorial/46uJdNaFUIDsUEAs/images/create-oidc-idp.png?fit=max&auto=format&n=46uJdNaFUIDsUEAs&q=85&s=dd9f3bbf95d4738c53d23e4144b921ca" alt="Pangolin dashboard form for adding an OAuth2/OIDC identity provider" width="2822" height="2508" data-path="images/create-oidc-idp.png" />
</Frame>

In the OAuth2/OIDC Configuration, you'll need the following fields:

<ResponseField name="Client ID" type="string" required>
  The client identifier provided by your identity provider.
</ResponseField>

<ResponseField name="Client Secret" type="string" required>
  The client secret provided by your identity provider.
</ResponseField>

<ResponseField name="Authorization URL" type="string" required>
  The authorization endpoint URL from your identity provider.
</ResponseField>

<ResponseField name="Token URL" type="string" required>
  The token endpoint URL from your identity provider.
</ResponseField>

## Token Configuration

Use JMESPath to select attributes from the claims token. See [JMESPath](https://jmespath.org/) for more information on how to use JMESPath.

Determine how to access information from the claims token returned by the identity provider. This is used to map the user information from the identity provider to the user information in Pangolin.

<ResponseField name="Identifier Path" type="string" required>
  This must be unique for each user within an identity provider.

  **Example**: `sub` or `user_id`
</ResponseField>

<ResponseField name="Email Path" type="string">
  Path to the user's email address in the claims token.

  **Example**: `email`
</ResponseField>

<ResponseField name="Name Path" type="string">
  Path to the user's display name in the claims token.

  **Example**: `name` or `preferred_username`
</ResponseField>

<ResponseField name="Scopes" type="string">
  The scopes to request from the identity provider (not JMESPath; must be space-delimited strings).

  **Default**: `openid profile email`

  <Note>
    Generally, `openid profile email` is sufficient for most use cases.
  </Note>
</ResponseField>
