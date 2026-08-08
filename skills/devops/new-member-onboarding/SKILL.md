---
name: new-member-onboarding
title: New Member Onboarding (Los Galactique)
description: Full onboarding for a new community member — create Pterodactyl account, set up Paymenter billing, assign Discord roles/permissions, send welcome message.
tags: [pterodactyl, paymenter, discord, onboarding, community]
---

# New Member Onboarding

Add a new member to Jefe's Los Galactique community. End-to-end workflow across Pterodactyl, Paymenter, and Discord.

## Prerequisites
- New member's Discord user ID
- What game server / plan they're joining for
- Payment plan (if applicable)

## Workflow

### 1. Paymenter Account
Create the user in Paymenter:
```
mcp_paymenter_paymenter_admin(
  method='POST',
  path='users',
  body='{"first_name": "...", "last_name": "...", "email": "...", "password": "..."}'
)
```

### 2. Pterodactyl Account
Create user in Pterodactyl application API:
```
mcp_pterodactyl_pterodactyl_application(
  method='POST',
  path='users',
  body='{"email": "...", "username": "...", "first_name": "...", "last_name": "...", "password": "..."}'
)
```

### 3. Discord Role Assignment
Use the Discord API (mcp cineverse or direct API) to assign appropriate roles:
- Member role
- Any plan-specific roles
- Verify via XP system if they're known

### 4. Welcome Message
Send a welcome ping in the appropriate Discord channel with:
- Their game server access info
- Billing portal link (Paymenter)
- Support contact info
- Link to rules / getting-started

### 5. Verify Access
- Confirm they can log into Pterodactyl
- Confirm they appear in Paymenter
- Confirm Discord roles are set

## Pitfalls
- Ask Jefe for the Discord channel to send the welcome message in
- Generate a random secure password for initial access
- Always email the credentials to the new member (or Jefe can relay)
- Check if user already exists in Pterodactyl/Paymenter first (duplicate prevention)
- If it's a free member, skip Paymenter step
