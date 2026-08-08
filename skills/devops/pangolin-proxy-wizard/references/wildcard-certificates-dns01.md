# Wildcard Certificates via DNS-01 (Pangolin + Cloudflare)

## Context

Jefe manages three domains (jefe.al, jefe.ovh, losgalactique.fr) all on Cloudflare DNS. Creating 50+ individual subdomains means 50+ Let's Encrypt certs, hitting rate limits. Solution: one wildcard cert per domain via DNS-01 challenge.

## Domain-to-org mapping

| Domain | ID | Notes |
|--------|----|-------|
| jefe.al | `ykx3vzina5zahuf` | Personal, all homelab services |
| losgalactique.fr | `51vbysoaydeg6cr` | Public games hosting |
| jefe.ovh | `domain1` | Older domain, some services |

## Cloudflare API token

- Required permissions: `Zone:Read` + `DNS:Edit`
- Created at: https://dash.cloudflare.com/profile/api-tokens
- Token is set as `CLOUDFLARE_DNS_API_TOKEN` env var on the traefik Docker service

## Config changes on Pangolin server (Hetzner CX23)

### 1. `docker-compose.yml` — Add to traefik service:

```yaml
  traefik:
    environment:
      CLOUDFLARE_DNS_API_TOKEN: "<redacted>"
```

### 2. `config/traefik/traefik_config.yml` — Replace HTTP-01 with DNS-01:

```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      dnsChallenge:
        provider: "cloudflare"
      email: "<acme-email>"
      storage: "/letsencrypt/acme.json"
      caServer: "https://acme-v02.api.letsencrypt.org/directory"
```

Remove the old `httpChallenge` section entirely — keeping both causes resolver conflicts.

### 3. `config/config.yml` — Prefer wildcard:

```yaml
domains:
  ykx3vzina5zahuf:
    base_domain: "jefe.al"
    prefer_wildcard_cert: true
    cert_resolver: "letsencrypt"
```

Repeat for each domain.

### 4. Restart:

```bash
docker compose down && docker compose up -d
docker compose logs -f traefik
```

Traefik should log: `ACME certificate generation completed for *.jefe.al`

## Verification

- New subdomains get SSL "Valid" instantly instead of "Pending"
- No more per-resource cert requests to Let's Encrypt
- 1 cert per domain total, not 1 per subdomain

## Gotchas

- **DNS-01 only**: HTTP-01 cannot issue wildcards. Must switch resolver.
- **Two-resolver pattern**: If some routes need HTTP-01 and others DNS-01, define both resolvers in traefik_config.yml and assign `cert_resolver` per-domain in config.yml. Default resolver applies if unset.
- **`config.yml` changes survive container restarts** but `traefik_config.yml` requires full `docker compose down && up`.
- **Pangolin dashboard domains tab**: After config change, the UI may still show old resolver. Ignore — Traefik runtime config shows the real state.
- **Cloudflare API key rotation**: Update `docker-compose.yml` and `docker compose up -d` (no down needed for env var changes).
