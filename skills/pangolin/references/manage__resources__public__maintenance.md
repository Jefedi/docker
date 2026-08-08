> ## Documentation Index
> Fetch the complete documentation index at: https://docs.pangolin.net/llms.txt
> Use this file to discover all available pages before exploring further.

# Maintenance Page

> Show a maintenance page to users when a resources is down for maintenance or targets are unhealthy

<div />

<Note>
  Maintenance pages are only available in [Enterprise Edition](/self-host/enterprise-edition).
</Note>

Pangolin can display a customizable maintenance page to users when a resource is undergoing maintenance or when all targets are unhealthy. This ensures users are informed about the downtime and provides a better user experience.

<Frame caption="Maintenance Page Preview">
  <img src="https://mintcdn.com/fossorial/WimeXubsTkPlCmpZ/images/maintenance_page.png?fit=max&auto=format&n=WimeXubsTkPlCmpZ&q=85&s=1947d7c701d51562591410339eafccc6" alt="Maintenance Page Preview" width="1386" height="875" data-path="images/maintenance_page.png" />
</Frame>

## Configuration

Title: The main title text displayed on the maintenance page.

Message: A descriptive message informing users about the maintenance status.

Estimated completion time: Optionally provide an estimated time for when the resource will be back online.

## Enabling Maintenance Page

To enable the maintenance page for a resource, navigate to the general resource settings in the Pangolin dashboard. Under the "Maintenance Page" section, you can customize the title, message, and estimated completion time. This can also be set using Blueprints.

## When is the Maintenance Page Shown?

There are two modes that control when the page is shown:

#### Forced

In forced mode, the maintenance page is displayed to all users regardless of the health status of the resource targets. This is useful for planned maintenance windows.

#### Automatic

In automatic mode, the maintenance page is shown only when all targets associated with the resource are unhealthy or all of the sites are offline. This is useful for unplanned outages and can be used to inform the user that the resource is temporarily unavailable by customizing the above settings.

## Remote Nodes

Maintenance pages do not work on remote nodes at this time.
