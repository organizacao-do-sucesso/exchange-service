# exchange-service

FastAPI implementation of the Exchange API: `GET /exchanges/{from}/{to}`
(also served at `/exchange/{from}/{to}`), plus `GET /health`.

Rates come from **PTAX**, the public API of the Central Bank of Brazil (BCB),
following the BACEN option of the course
(<https://insper.github.io/platform/pt/2026.2/exercises/exchange/bacen/>).
PTAX quotes every currency in BRL, so a pair such as USD -> EUR is a cross rate
through BRL. Rates are cached in Redis; if Redis is down the service calls PTAX
directly.

| Variable | Default | Meaning |
|---|---|---|
| `EXCHANGE_API_URL` | PTAX URL | base URL of the PTAX OData API |
| `EXCHANGE_API_TIMEOUT_SECONDS` | `3` | timeout of each PTAX call |
| `EXCHANGE_CACHE_TTL_SECONDS` | — | how long a rate stays in Redis (300 recommended) |
| `REDIS_HOST` / `REDIS_PORT` | — | Redis address |

Kubernetes manifests live in [`k8s/`](k8s) and are consumed remotely by
`k8s/base` of the `platform` repository.
