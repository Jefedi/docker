---
name: pangolin
description: >
  Pangolin ZTNA documentation expert. Covers self-hosting, Newt sites, Gerbil
  tunnels, Olm clients, Traefik reverse proxy, config.yml, DNS/networking,
  public/private resources, SSO/IdP, CrowdSec, wildcard certs, integration API,
  blueprints, remote nodes, and troubleshooting. Trigger words: pangolin, newt,
  gerbil, olm, traefik, reverse proxy, tunnel wireguard, site, resource, ZTNA,
  crowdsec, ZTNA, zero trust, site-to-cloud, backhaul.
---

# Pangolin Documentation Skill

## Mental Model

Pangolin is a zero-trust access (ZTNA) platform: a control plane (Pangolin server + Gerbil tunnel relay + Traefik reverse proxy) manages **Sites** (remote networks connected via the Newt connector) and **Resources** (network addresses you expose). **Clients** (Olm) connect users to private resources over WireGuard tunnels. Public resources are reverse-proxied through Traefik with TLS and auth. Private resources are only reachable through a connected client over the tunnel. Sites, resources, and clients are org-scoped. The config.yml file on the server controls global behavior; Newt and Olm have their own config files on their respective hosts.

## Routing Table

Load the reference file that matches the question domain. Always open the file before answering.

| Question domain | Reference file |
|---|---|
| Architecture overview, how it works | `about__how-pangolin-works.md` |
| Pangolin vs VPN vs reverse proxy | `about__pangolin-vs-reverse-proxy-vs-vpn.md` |
| System architecture (control plane, nodes, connectors) | `development__system-architecture.md` |
| Quick install (automated) | `self-host__quick-install.md` |
| Manual Docker Compose install | `self-host__manual__docker-compose.md` |
| Podman / Unraid / K8s install | `self-host__manual__podman-quadlets.md`, `self-host__manual__unraid.md`, `self-host__manual__kubernetes__overview.md` |
| config.yml (server, all options) | `self-host__advanced__config-file.md` |
| privateConfig.yml (enterprise) | `self-host__advanced__private-config-file.md` |
| Docker container layout, volumes, config path | `self-host__manual__docker-compose.md` |
| DNS & networking (domain setup, records) | `self-host__dns-and-networking.md` |
| Domains (types, config) | `manage__domains.md` |
| Wildcard domains / DNS-01 certs | `self-host__advanced__wild-card-domains.md` |
| Cloudflare proxy mode | `self-host__advanced__cloudflare-proxy.md` |
| Without tunneling (local reverse proxy only) | `self-host__advanced__without-tunneling.md` |
| Sites — understanding, install, configure | `manage__sites__understanding-sites.md`, `manage__sites__install-site.md`, `manage__sites__configure-site.md` |
| Sites — credentials, provisioning keys, auto-update | `manage__sites__credentials.md`, `manage__sites__site-provisioning.md`, `manage__sites__auto-update.md` |
| Clients (Olm) — install, configure | `manage__clients__install-client.md`, `manage__clients__configure-client.md` |
| Clients — NAT traversal, firewalls, logs | `manage__clients__nat-traversal.md`, `manage__clients__firewalls.md`, `manage__clients__client-logs.md` |
| preferLocalRoutes, DNS Over Tunnel, aliases | `manage__clients__configure-client.md` |
| Public resources — HTTP/HTTPS | `manage__resources__public__http-https.md` |
| Public resources — TCP/UDP raw | `manage__resources__public__raw-resources.md` |
| Public resources — RDP, VNC, SSH (browser) | `manage__resources__public__rdp.md`, `manage__resources__public__vnc.md`, `manage__resources__public__ssh.md` |
| Public resources — auth, rules, policies | `manage__resources__public__authentication.md`, `manage__access-control__rules.md`, `manage__resources__public__resource-policies.md` |
| Public resources — targets, health checks, failover | `manage__resources__public__targets.md`, `manage__resources__public__healthchecks-failover.md` |
| Public resources — wildcard, maintenance page | `manage__resources__public__wildcard-resources.md`, `manage__resources__public__maintenance.md` |
| Private resources — understanding, host, CIDR | `manage__resources__understanding-resources.md`, `manage__resources__private__host.md`, `manage__resources__private__cidr.md` |
| Private resources — HTTP/HTTPS, SSH | `manage__resources__private__private-http.md`, `manage__resources__private__ssh.md` |
| Private resources — alias, destinations, ports/ICMP | `manage__resources__private__alias.md`, `manage__resources__private__destinations.md`, `manage__resources__private__port-restrictions.md` |
| Private resources — auth, multi-site routing | `manage__resources__private__authentication.md`, `manage__resources__private__multi-site-routing.md` |
| SSO / IdP — add provider, OIDC, Google, Azure | `manage__identity-providers__add-an-idp.md`, `manage__identity-providers__openid-connect.md`, `manage__identity-providers__google.md`, `manage__identity-providers__azure.md` |
| SSO — auto-provisioning | `manage__identity-providers__auto-provisioning.md` |
| Access control — MFA, sessions, passwords, approvals | `manage__access-control__mfa.md`, `manage__access-control__session-length.md`, `manage__access-control__approvals.md`, `manage__access-control__change-password.md` |
| Access control — users/roles, forwarded headers, links | `manage__access-control__create-user.md`, `manage__access-control__forwarded-headers.md`, `manage__access-control__links.md` |
| Access control — security keys, login page, password rotation | `manage__access-control__security-keys.md`, `manage__access-control__login-page.md`, `manage__access-control__password-rotation.md` |
| Integration API (REST) | `manage__integration-api.md`, `self-host__advanced__integration-api.md` |
| Common API routes | `manage__common-api-routes.md` |
| Blueprints (declarative resources) | `manage__blueprints.md`, `manage__community-blueprints-repo.md` |
| Remote nodes — understanding, install, config | `manage__remote-node__understanding-nodes.md`, `manage__remote-node__quick-install-remote.md`, `manage__remote-node__config-file.md` |
| Remote nodes — site-to-cloud backhaul | `manage__remote-node__backhaul.md` |
| CrowdSec integration | `self-host__community-guides__crowdsec.md` |
| Traefik log rotation (CrowdSec) | `self-host__advanced__traefik-log-rotation.md` |
| Geo-blocking, ASN blocking | `manage__geoblocking.md`, `manage__asnblocking.md`, `self-host__advanced__enable-geolocation.md`, `self-host__advanced__enable-asn-lookup.md` |
| Alerting — alert rules, health checks | `manage__alerting__alert-rules.md`, `manage__alerting__health-checks.md` |
| Analytics — auth/action/network/request logs | `manage__analytics__access.md`, `manage__analytics__action.md`, `manage__analytics__connection.md`, `manage__analytics__request.md` |
| Event streaming (HTTP webhook, S3) | `manage__analytics__streaming.md`, `manage__analytics__streaming__http.md`, `manage__analytics__streaming__s3.md` |
| Branding, labels, org ID | `manage__branding.md`, `manage__labels.md`, `manage__organizations__org-id.md` |
| Database options (SQLite/Postgres) | `self-host__advanced__database-options.md` |
| Clustering / HA | `self-host__advanced__clustering.md` |
| Metrics & observability | `self-host__advanced__observability.md`, `self-host__community-guides__metrics.md` |
| Update Pangolin | `self-host__how-to-update.md` |
| Internal CLI (pangctl) | `self-host__advanced__container-cli-tool.md` |
| Enterprise edition | `self-host__enterprise-edition.md` |
| Choosing a VPS | `self-host__choosing-a-vps.md` |
| Endpoints & relays (Cloud allowlists) | `manage__endpoints-and-pops.md` |
| SSH access (public + private) | `manage__ssh.md` |
| Community guides index | `self-host__community-guides__overview.md` |
| Bypass rules (community) | `self-host__community-guides__rules.md` |
| K8s troubleshooting (Pangolin, Newt) | `self-host__manual__kubernetes__pangolin__troubleshooting.md`, `self-host__manual__kubernetes__newt__troubleshooting.md` |
| **Jefe's field knowledge (gotchas)** | `00-gotchas-jefe.md` |

## Behavior Rule

**Never answer from memory about a configuration option, default value, or API field.** Always open the corresponding reference file and cite the exact value. If the answer is not in the aspirated files or the gotchas file, say so explicitly. Do not invent.