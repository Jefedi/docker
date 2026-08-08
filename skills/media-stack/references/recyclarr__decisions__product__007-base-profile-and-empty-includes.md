# PDR-007: Base Profile and empty CF group includes

- **Status:** Proposed
- **Date:** 2026-04-29
- **Upstream:** [Discord thread][upstream] in TRaSH Guides third-party sync tools channel

[upstream]: https://discord.com/channels/492590071455940612/833801961043394660/1498324953349492767

## Context

PR #2711 added many new CF groups to TRaSH Guides, along with a "Base Profile" in a new "TEST"
quality profile group. About 84% of all CF groups now reference this Base Profile in their
`quality_profiles.include` section.

The Base Profile exists because the CF groups JSON schema (`cf-groups.schema.json`) has
`minProperties: 1` on `quality_profiles.include`, which means every group must reference at least
one profile. Groups that aren't tied to any real guide profile (audio channels, optional
resolutions, language-specific filters, etc.) need somewhere to point, so they point at Base
Profile.

The schema was introduced in PR #2628, which was AI-generated. The `minProperties: 1` constraint was
likely a default based on the data at the time (all existing groups already had profile references),
not a deliberate design decision. A TRaSH Guides contributor confirmed the Base Profile was created
specifically because "I can't add a group without assigning it to a profile." The contributor also
uses a GUI tool (built by the Clonarr developer) for authoring profiles and groups, which enforces
the same constraint.

The contributor explained the schema rule is a safeguard against missing or wrong hashes in profile
references, which had caused issues before. The concern is valid, but the solution puts the
workaround in the permanent guide data rather than in the authoring/review process.

## Recyclarr's position

The tradeoff isn't justified. The problem being solved (catching missing hashes during authoring)
belongs in the PR/merge process, not in the data itself. The Base Profile adds complexity that
ripples downstream:

- The `config-templates` repo needed `EXCLUDED_PROFILE_GROUPS = {"TEST"}` in its template generation
  script to filter out the Base Profile.
- Every sync tool that reads `quality-profile-groups/groups.json` now has to decide what to do with
  a profile group that isn't meant to be synced.
- The guide data contains a profile whose description is "This is a base profile that we use for
  testing," which is confusing for anyone reading the raw JSON.

Recyclarr doesn't require `quality_profiles.include` to be non-empty. An empty `include` would mean
the group never auto-syncs (no profile trash_ids to match against), but users could still explicitly
add it via `custom_format_groups.add`. This is the correct behavior for groups that genuinely don't
belong to any guide profile.

There are ways to catch missing hashes during the PR/merge process without affecting the actual
data. The contributor didn't respond to this point directly.

## Decision

No Recyclarr code changes needed. The Base Profile is harmless at runtime because auto-sync matching
is strictly by trash_id, and no user would configure a profile pointing at the Base Profile. The
`config-templates` repo already has a workaround in place.

If TRaSH Guides relaxes the schema constraint in the future, Recyclarr would benefit from the
simplification (the `EXCLUDED_PROFILE_GROUPS` workaround could be removed), but this isn't worth
pursuing further unless the upstream position changes.

## Affected areas

- Config: None
- Commands: None
- Migration: Not required

## Consequences

- The `config-templates` generation script carries an exclusion for the TEST profile group. This is
  a minor maintenance burden but not a blocking issue.
- If more "internal" profile groups appear upstream in the future, the exclusion list in
  `config-templates` would need to grow. Worth revisiting if that happens.
- Recyclarr's auto-sync logic is unaffected; Base Profile references are silently ignored because
  they don't match any user-configured profile.
