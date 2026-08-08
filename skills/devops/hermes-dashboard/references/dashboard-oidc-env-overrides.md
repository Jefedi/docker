# Reference: OIDC environment variable precedence
# The Hermes dashboard runs in a Docker container using s6 as init.
# Environment variables for OIDC are injected from two sources:
#   1. `/run/s6/container_environment/` – these come from the s6 service definition and
#      have higher priority than values read from a `.env` file or the global
#      `config.yaml`.
#   2. The `.env` file and/or `config.yaml` – loaded at startup but overridden
#      if a variable is present in (1).
# 
# In practice this means:
#   * If you set `HERMES_DASHBOARD_OIDC_*` in the s6 container definition,
#     those values win and the dashboard will **always** use OIDC.
#   * To disable OIDC and fall back to basic auth, simply **clear** all the
#     `HERMES_DASHBOARD_OIDC_` variables in the container definition.  This
#     overrides any values that might have been set in the `.env` file.
#   * The `.env` file is an easy way to enable OIDC on a *per‑instance* basis
#     when you run the dashboard in a custom environment, but you must be
#     careful not to have conflicting definitions in the s6 config.

# Example usage:
#   1. For a public deployment:  leave the s6 OIDC env vars unset; set
#      `HERMES_DASHBOARD_OIDC_*=''` or remove them entirely.
#   2. For a private deployment with OIDC:  set the full set of OIDC env
#      vars *in the s6 definition* to guarantee they are used.

# This file is intended as a quick reference for devops and troubleshooting
# efforts.  It should be referred to when modifying s6 service configs.
