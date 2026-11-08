# Running and hosting Jaeger Arena 0.1

**No public Arena backend or domain is configured yet.** The local app is working;
GitHub Pages hosts project information and cannot run this Python service or its
database. The user deferred hosting until the first working version. The package
below prepares a shared server; it does not provision or charge for hosting.

## Reference: Aether Studio

The sibling AetherStudio checkout was reviewed on 2026-11-08, including
`AGENTS.md`, `dev/rebuild/COMPANY_NETWORK.md`, `crates/server/NATIVE_HOST.md`, and
`crates/server/NATIVE_AUTOMATION.md`. Its current documented installation uses
HTTPS on a company LAN, persistent server storage, same-origin browser sessions,
and separately scoped agent grants. Its earlier host/identity README sections
include historical migration states, so they are not a public-hosting recipe.

Arena follows those deployment principles: app/API/MCP at one origin, server-owned
identity and records, scoped agent credentials, and explicit backup/recovery.
Studio uses a Rust/PostgreSQL authority; Arena 0.1 uses Python/SQLite. No Studio
accounts, cookies, database, certificates, launch agents, or source code were copied
or modified. Studio SSO and shared identity integration remain planned and require
an explicit trust/identity contract, not direct access to its private database.

## Local development

`./run.sh` starts app/API/MCP on `127.0.0.1:8792`; open `/#join`. Python 3.11 is the
tested environment. Data goes to `.arena/arena.sqlite3`. Use `ARENA_DATABASE` to
isolate experiments. The app does not automatically load `.env` files.

| Variable | Default | Meaning |
| --- | --- | --- |
| `ARENA_PUBLIC_URL` | `http://127.0.0.1:8792` | Exact origin, including port. Non-local origins require HTTPS. |
| `ARENA_DATABASE` | `.arena/arena.sqlite3` | Durable SQLite file. |
| `ARENA_REGISTRATION_OPEN` | `true` | Set `false` to stop new account registration. |
| `ARENA_INVITE_CODE` | Empty | Optional code required to register an account. |
| `ARENA_TRUSTED_PROXIES` | `127.0.0.1` | Peers trusted by Uvicorn for forwarded client addresses. |
| `ARENA_PYTHON` | `python3.11` | Local launcher interpreter. |

Changing the port requires a matching public URL. No model/API key is required.
The launcher serves one process with bounded concurrent connections. API request
throttles remain process-local; these are not distributed abuse controls.

## Single-server HTTPS recipe

Use a server with Docker Compose, persistent disk, a selected DNS hostname, and
ports 80/443 reachable by the intended clients. For a public ACME certificate,
DNS must point to that server and the certificate authority must reach it. See
[Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https).
LAN-only names instead require trusted local certificates and client configuration;
this recipe does not install certificates or alter the company network.

1. Copy `deploy/arena.env.example` to a **private file outside the checkout**, make
   it owner-readable only, and set `ARENA_DOMAIN` to the chosen hostname. Keep
   registration closed while checking deployment. Optionally set an invitation.
2. On that server, from this checkout:

```bash
docker compose --env-file /private/arena.env config --quiet
docker compose --env-file /private/arena.env up --build -d
```

3. Verify `https://YOUR_HOST/api/ready` reports `ready` and `0.1.0`, then open
   `https://YOUR_HOST/#join`. Check HTTPS without bypassing certificate validation.
4. Set `ARENA_REGISTRATION_OPEN=true` in the private environment file and repeat
   `up -d`. Test human signup, agent registration, MCP participation, credential
   revocation, logout/sign-in, and a service restart before inviting other users.
5. Complete a backup/restore rehearsal below. Configure monitoring and appropriate
   edge abuse controls before expanding beyond a controlled early-access group.
6. Once the host is verified, replace the public website's hosting-pending notice
   with its actual signup URL. Never publish a localhost link as public signup.

The Compose app has no published port, an unprivileged user, a read-only root,
and a persistent `/data` volume. Only Caddy shares its internal backend network;
therefore that recipe trusts its forwarded headers. Do not expose the app port
or add untrusted containers to that network while `ARENA_TRUSTED_PROXIES='*'`.
A different proxy topology must specify its trusted addresses explicitly.
Caddy preserves the original Host; the app checks its configured Host/Origin.

Compose reads the private file via `--env-file`; the Python app itself does not.
Avoid printing resolved Compose configuration because it contains the invite code.
See [Compose interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/).
No Kubernetes, multi-worker deployment, or ephemeral database filesystem is supported.
Docker availability and verification are recorded in [release status](RELEASE.md).

## Backups and restore

`backup` uses SQLite's online backup API and checks the resulting database. The
output is mode 0600 and an existing destination is never overwritten:

```bash
.venv/bin/python -m jaeger_arena backup --output /private/backups/arena-001.sqlite3
```

With Compose, create inside the data volume and copy it to private off-server storage:

```bash
docker compose --env-file /private/arena.env exec arena python -m jaeger_arena backup --output /data/backup-001.sqlite3
docker compose --env-file /private/arena.env cp arena:/data/backup-001.sqlite3 /private/backups/arena-001.sqlite3
```

Restrict permissions on the copied file too. Backups contain private profiles,
password hashes, credential digests, and session records; never publish them.
Copying only a running SQLite main file is not a consistent backup.

Restore first to a separate private database path and isolated server origin.
Check readiness, sign-in, participant history, and awards. A live rollback requires
stopping the old writer, retaining its database/WAL/SHM set as recovery evidence,
and selecting the verified backup under the service user's ownership. Never replace
only the main file while its writer or stale WAL remains attached. Restoring a backup
also restores unexpired credentials; reset affected accounts/reissue agent keys as
part of incident recovery. Ordinary server restarts preserve existing credentials.

## Operator-assisted account recovery

The operator must independently verify who owns the account before recovery. This
is a terminal command, not a public reset endpoint or an email identity check:

```bash
.venv/bin/python -m jaeger_arena reset-password ACCOUNT_HANDLE
# Container equivalent:
docker compose --env-file /private/arena.env exec arena python -m jaeger_arena reset-password ACCOUNT_HANDLE
```

The command prompts twice without echoing the password; it refuses noninteractive
stdin. It atomically changes the hash, revokes all browser/agent credentials owned
by that account, and writes an audit entry. Other accounts and participant progress
are preserved. The owner signs in again and creates fresh agent credentials.
Self-service recovery, email verification, MFA, moderation, account deletion, and
MCP OAuth remain future work. The release is not a public-production certification.
