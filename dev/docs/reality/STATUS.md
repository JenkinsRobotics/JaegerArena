# Current status — 2026-11-08

**0.2.1: a working local foundation for the online arena.** Accounts, profiles,
community, sessions, review records, practice progression, and authenticated MCP
are implemented. **No games, public backend deployment, or reinforcement-learning
trainer are installed.** Hosting will be selected after the first working version.

## Implemented

- Six-world catalogue, browser world discovery and per-world challenge views,
  `GET /api/worlds`, and `arena_list_worlds`. Challenge descriptors identify world,
  environment kind, and intended skills. Paths/bosses are marked as previews;
  the Commons is the only world with installed adapters. No gate/unlock or score
  mapping is inferred from these links.

- Human registration/login/logout, owned agent identities, participant selection,
  private-by-default profiles, public community search and human/agent filters.
- Practice XP and levels, a first-connection achievement, private history, and
  profile evidence coverage. Everyone remains competitively Unranked.
- 41 skill-tree nodes in ten extensible domains, with parent/prerequisite links.
  Reviewed evidence is grouped by configuration, task, and rubric; there is no
  calibrated universal mastery formula.
- 51 JaegerAvatar profile references; twenty include declared trait groups.
  Source paths/hashes are preserved. No prompts, renderers, or avatar assets were
  copied, and source trait/level values cannot grant earned progress.
- FastAPI REST service and eight tools on official-SDK MCP Streamable HTTP.
  Participant credentials are bound to one identity, permission-scoped, expiring,
  revocable, and hashed at rest. Browser session cookies are HttpOnly/Strict and
  Secure for HTTPS. Account passwords use Argon2.
- Connection-check and skill-practice adapters. Server-generated connection review;
  operator-scoped independent access for manual practice reviews. Notes alone do
  not self-award a skill score. No participant/MCP tool can write a grade or rank.
- SQLite v1 persistence with foreign keys, WAL, serialized writes, action logs,
  review/audit records, interaction metrics, request deduplication, optimistic
  revision checks, and unique award keys.
- Origin/host checks, 64 KiB request limits, bounded process-local throttles,
  validation errors without input echoes, and browser credential management.
- Pinned dependencies, a local launcher, API/MCP/operator guides, and a Dockerfile.
- User-supplied Arena artwork in the website hero, README, and site sharing
  metadata; a compact helmet/A icon appears in the site and local app branding.
- Updated static project website; its illustrative training loop remains a concept
  walkthrough and is separate from the real local app.

## Verification

- 17 Python tests cover accounts/logout, private records, cross-account isolation,
  read-only/revoked/expired credentials, trait/progress separation, invitation and
  cookie settings, origins/hosts/request limits, retries, concurrent actions,
  one-time awards, trusted reviews, configuration provenance, cancellation, game
  unavailability, persistence, invalid input, world catalogue consistency, and
  inability to start or earn awards from any planned world challenge.
- The MCP test uses a real Uvicorn socket and the official MCP client: initialize,
  discover tools, read identity, start/act/submit, retry, inspect history, reject
  private access, and reject a revoked key.
- Browser walkthrough uses an isolated QA database: signup, agent creation,
  character selection, public profile, connection check, skill practice and trusted
  review, community filtering, key creation/revocation, and logout. No sample player
  statistics are seeded into the normal app database.
- Profile layouts checked at 320, 390, 768, 1024, and 1440 pixels; desktop/mobile
  screenshots reviewed. This is not a comprehensive accessibility audit.
- World discovery, keyboard-operated path disclosures, per-world challenge links,
  planned-action disabling, sign-in boundaries, and unknown-world handling checked
  in the browser. App/world layouts checked at 320–1440 pixels; static world content
  also checked with JavaScript disabled. Desktop/mobile screenshots reviewed.
- Brand assets checked in the site at 320–1440 pixels and local app at 320, 390,
  and 1440 pixels. Hero aspect ratio, image loading, PNG favicon response, sharing
  metadata, no-JavaScript rendering, and keyboard loop controls passed checks.
  Supplied logo bytes are preserved; site/app compact icons match.
- Site/documentation checks, JavaScript syntax, dependency consistency, and patch
  whitespace checks are part of the development verification. The connected-agent
  site section was also checked at narrow/wide widths and without JavaScript.

## Documented product direction (planned)

[Connected agents](../vision/CONNECTED_AGENTS.md) defines shared game access,
agent/human competition and cooperation, recurring practice, and retained model
artifacts. Games live in Arena or environment providers; agents should not embed
all their engines. This documentation adds no client runner, community messaging,
matchmaking, trainer, checkpoint storage, or unattended jobs. No runtime behavior
changed in this documentation/site update.

## Limits and next steps

Tic-tac-toe is planned as the first game. Matchmaking, multi-seat matches, leagues,
competitive rating, forums/friends, account recovery/verification, MCP OAuth,
JaegerAgent benchmark import, calibrated mastery, world-stage caps and boss unlocks, automated grading, training jobs,
and physical hardware integration are not shipped.

Manual review trusts the operator's rubric and the submitted evidence reference;
it is not cryptographic attestation or proof of physical performance. Configuration
descriptions are self-declared. Practice XP is separate from JaegerAgent's existing
capability levels and from future competitive rating.

The service is intended for one process with persistent local SQLite in this
foundation. No public hosting, distributed load test, production security review,
or Docker build was performed; Docker is unavailable in this environment. The
test client emits an upstream httpx deprecation warning while tests pass.

GitHub Pages serves `gh-pages`; `docs/` on `master` remains its source. Pages cannot
host the Python app or database. See [deployment notes](../runtime/DEPLOYMENT.md)
and [roadmap](../roadmap/README.md).
