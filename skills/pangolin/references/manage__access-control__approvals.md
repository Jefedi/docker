> ## Documentation Index
> Fetch the complete documentation index at: https://docs.pangolin.net/llms.txt
> Use this file to discover all available pages before exploring further.

# Device Approvals

> Only allow trusted devices to connect to an organization

<div />

<Note>
  Only available in [Pangolin Cloud](https://app.pangolin.net/auth/signup) and [Enterprise Edition](/self-host/enterprise-edition).
</Note>

By default, any client configured with valid credentials can connect to an organization. To enhance security, you can enable device approvals, which require each new device to be manually approved by an administrator before it can connect.

When device approvals are enabled, the first time a user connects a new device to the organization, the device will be marked as "Pending Approval." An administrator must then review and approve the device in the management console before it can access organization resources.

<Frame>
  <img src="https://mintcdn.com/fossorial/VqiOoRUR8g1Tf03J/images/device_waiting_approval.png?fit=max&auto=format&n=VqiOoRUR8g1Tf03J&q=85&s=74238fab8ebb39dbafa5a29b57176df4" alt="Device marked pending approval in the Pangolin dashboard" width="1617" height="833" data-path="images/device_waiting_approval.png" />
</Frame>

All approvals can also be managed from a central page as they stream in to allow admins to approve or deny devices quickly.

<Frame>
  <img src="https://mintcdn.com/fossorial/VqiOoRUR8g1Tf03J/images/approvals_page.png?fit=max&auto=format&n=VqiOoRUR8g1Tf03J&q=85&s=d6b11a0954136d4868b4a789f51931d2" alt="Approvals page listing pending devices in the Pangolin dashboard" width="1577" height="391" data-path="images/approvals_page.png" />
</Frame>

## Enabling Device Approvals

Device approvals are enabled on a per-role basis. To enable device approvals for a role, follow these steps:

1. Click on the **Roles** tab.
2. Select the role you want to enable device approvals for.
3. Toggle the **Require Device Approval** option to enable it.
4. Save your changes.

Once enabled, any new user connecting with that role will require approval from an administrator before it can access organization resources.

<Tip>
  You cannot enable device approvals for the "Admin" role.
</Tip>
