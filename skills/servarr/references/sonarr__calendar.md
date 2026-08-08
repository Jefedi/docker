---
title: Sonarr Calendar
description: View upcoming and aired episodes in a calendar format for better scheduling
tags:
  - sonarr
  - calendar
  - schedule
  - episodes
  - planning
---

# Calendar

The calendar shows you recently aired episodes, as well as upcoming episodes.

# iCal Feed

- Sonarr can provide your calendar as an iCal feed. This will contain the previous [7 days](https://github.com/Sonarr/Sonarr/blob/main/src/Sonarr.Api.V3/Calendar/CalendarFeedController.cs) and the next [28 days](https://github.com/Sonarr/Sonarr/blob/main/src/Sonarr.Api.V3/Calendar/CalendarFeedController.cs)

!!! warning
    Google Calendar has internal issues that results in it no longer updating. This is a Google issue and not a Sonarr issue. It can often be resolved by removing and re-adding the calendar.
