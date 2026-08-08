> ## Documentation Index
> Fetch the complete documentation index at: https://docs.pangolin.net/llms.txt
> Use this file to discover all available pages before exploring further.

# Custom Login Page

> Configure a custom authentication page URL for your organization

<div />

<Note>
  Custom auth pages are only available in [Pangolin Cloud](https://app.pangolin.net/auth/signup).
</Note>

Custom organization authentication pages let you serve the login page at your own domain instead of the default `app.pangolin.net`. This provides better user experience and brand consistency.

## Benefits

**For Resource Authentication:**

* Users are redirected to your custom domain for login
* Familiar domain builds trust and security awareness
* Consistent branding throughout the authentication flow

**For Identity Provider Integration:**

* Centralized login page for your organization
* Choose between multiple login methods (Google, Azure, etc.)
* Platform SSO: login once, access all Pangolin resources
* Direct access to the Pangolin management dashboard

<Frame>
  <img src="https://mintcdn.com/fossorial/TjYzFtLIcUWNEXlf/images/org-auth-page.png?fit=max&auto=format&n=TjYzFtLIcUWNEXlf&q=85&s=20ebc6fbe15ec122eeca41274630eaeb" alt="Organization login page with multiple login methods" width="1512" height="1072" data-path="images/org-auth-page.png" />
</Frame>

## Configuration

1. Go to **Settings** in your organization sidebar
2. Use the domain picker to select your custom domain
3. Save your changes

<Note>
  You need to add a custom domain to your organization first. Free domains (`*.tunneled.to`, `*.hostlocal.app`, etc.) cannot be used for auth pages. [Learn how to add domains](/manage/domains)
</Note>

<Frame>
  <img src="https://mintcdn.com/fossorial/TjYzFtLIcUWNEXlf/images/set-org-auth-page-domain.png?fit=max&auto=format&n=TjYzFtLIcUWNEXlf&q=85&s=e02c1885b52bb11d15abf8d97047813b" alt="Domain picker for the auth page in Pangolin settings" width="1252" height="498" data-path="images/set-org-auth-page-domain.png" />
</Frame>
