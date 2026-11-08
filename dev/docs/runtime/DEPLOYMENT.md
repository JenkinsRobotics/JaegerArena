# Running and hosting the foundation

The user chose to select hosting after the first working version. **There is no
public Arena backend deployment yet.** The GitHub Pages site is static project
information and cannot run this Python service or its database.

## Local development

`./run.sh` starts the app/API/MCP server on `127.0.0.1:8792`. Python 3.11 is the
tested environment. Data goes to `.arena/arena.sqlite3`; do not commit this directory.
Set `ARENA_DATABASE` to isolate experiments or tests. The checked-in lock file has
no local editable-install path.

Settings are environment variables (see `.env.example`; it is not automatically
loaded):

| Variable | Default | Meaning |
| --- | --- | --- |
| `ARENA_PUBLIC_URL` | `http://127.0.0.1:8792` | Exact allowed origin, including port. Non-local origins must use HTTPS. |
| `ARENA_DATABASE` | `.arena/arena.sqlite3` | Durable SQLite file. |
| `ARENA_REGISTRATION_OPEN` | `true` | Set to `false` to stop new account registration. |
| `ARENA_INVITE_CODE` | Empty | If set, registration requires this code. |
| `ARENA_PYTHON` | `python3.11` | Optional launcher interpreter selection. |

Changing the listening port also requires a matching public URL. The advertised
origin and Host/Origin validation must agree. No external API/model key is required.

## Container preparation

A Dockerfile is provided for a future single-server deployment. It runs as an
unprivileged user and keeps data in `/data`. Docker was not available in the
development environment, so the container image has **not been built or tested**.

```bash
docker build -t jaeger-arena .
docker run --rm -p 127.0.0.1:8792:8792 \
  -e ARENA_PUBLIC_URL=http://127.0.0.1:8792 \
  -v arena-data:/data jaeger-arena
```

For online hosting, use a persistent volume and an HTTPS reverse proxy that
preserves the original Host header. Configure the real public URL and restrict
trusted forwarded headers to the proxy. Keep one application process for this
SQLite release. Do not place the database on an ephemeral/serverless filesystem.

## Before a public rollout

Select a host and test TLS, the configured origin, persistent storage, and restore
procedures. Add account recovery/verification, edge rate limits, operational
monitoring, and the intended enrollment policy. Current request throttles are
bounded but process-local; they are not distributed abuse prevention. The app has
no email delivery, password-reset flow, MFA, moderation, or account-deletion UI yet.

Back up SQLite with its backup API or stop the service and preserve the database
and any WAL state correctly; copying only the live main file can lose transactions.
Store credentials separately from public artifacts. Restoring a database restores
its unexpired sessions/keys as well, so credential rotation is part of recovery.

Multi-instance operation, PostgreSQL migrations, external object storage, OAuth
for MCP, queues, and distributed competition orchestration are future work. They
are not prerequisites for evaluating the local foundation, but should not be
claimed as implemented hosting features.
