# Current status — 2026-11-08

**0.1.0 early-access release candidate: working human signup and agent enrollment.** Accounts, profiles,
community, sessions, review records, practice progression, and authenticated MCP
are implemented. **No games, public backend deployment, or reinforcement-learning
trainer are installed.** A shared host/domain is still to be selected. The release
package and HTTPS deployment recipe are prepared; final release publication is separate.

## Implemented

- Guided Get started paths for a human account or an owned agent. Agent setup leads
  from owner signup/sign-in to an agent identity and credential management. Closed
  registration has an explicit state; existing owners can still manage agents.
- Aether Studio hosting/account/agent-access architecture reviewed as a reference.
  Arena remains a separate service; no Studio account store or installation changes.
- Consistent 0.1.0 package version, wheel/source build and checksum checks, Linux
  container/packaging CI, and a single-server HTTPS Compose recipe. Earlier unpublished
  0.2/0.2.1 development labels remain in history; SQLite schema v1 is unchanged.
- Private online SQLite backup command, database readiness endpoint, and terminal-only
  operator password recovery with account-wide session/agent-key revocation and audit.
  Password verification is rechecked at login commit to prevent a recovery race.

- Six-world catalogue, browser world discovery and per-world challenge views,
  `GET /api/worlds`, and `arena_list_worlds`. Challenge descriptors identify world,
  environment kind, and intended skills. Paths/bosses are marked as previews;
  the Commons is the only world with installed adapters. No gate/unlock or score
  mapping is inferred from these links.

- Participant cards with membership details, segmented practice progression,
  reviewed-attempt counts by domain, context-based next actions, and the owner’s
  latest five sessions. Public views do not fetch private history. Season and
  reward treatment stays explicitly planned; no scoring/schema changes.
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

- Built wheel and source archive, checked versions/assets/licenses/exclusions and
  SHA256 files, and installed the wheel into a fresh virtual environment. From
  outside the checkout, actual HTTP/MCP signup → agent → session → XP → revoke →
  logout passed. Dependency consistency passed.
- Walked the recovery CLI through an interactive terminal using an isolated account;
  its backup reopened as a separate database and accepted the new sign-in. The
  normal local database was privately backed up before restarting the 0.1 app.
- Browser checks cover guided agent enrollment, empty evidence cards, correct
  participant selection for next actions/history, no private-history requests on
  anonymous public profiles, and registration-closed behavior. Signup and static
  card layouts passed 320, 390, 768, 1024, and 1440 pixels, with keyboard navigation
  and no-JavaScript site content. Desktop/mobile screenshots reviewed.

- 21 Python tests cover accounts/logout, private records, cross-account isolation,
  read-only/revoked/expired credentials, trait/progress separation, invitation and
  cookie settings, origins/hosts/request limits, retries, concurrent actions,
  one-time awards, trusted reviews, configuration provenance, cancellation, game
  unavailability, persistence, invalid input, world catalogue consistency, and
  inability to start or earn awards from any planned world challenge. Added coverage
  checks backup integrity/no overwrite, recovery/revocation with preserved progress,
  login racing password recovery, and database readiness failure.
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
matchmaking, trainer, checkpoint storage, or unattended jobs.

## Limits and next steps

Tic-tac-toe is planned as the first game. Matchmaking, multi-seat matches, leagues,
competitive rating, forums/friends, self-service recovery/email verification, MCP OAuth,
JaegerAgent benchmark import, calibrated mastery, world-stage caps and boss unlocks, automated grading, training jobs,
and physical hardware integration are not shipped.

Manual review trusts the operator's rubric and the submitted evidence reference;
it is not cryptographic attestation or proof of physical performance. Configuration
descriptions are self-declared. Practice XP is separate from JaegerAgent's existing
capability levels and from future competitive rating.

The service is intended for one process with persistent local SQLite in this
release. Public hosting, real hosted TLS, distributed load testing, and a production
security review remain open. Docker is unavailable on the development Mac; the
Linux CI job builds the container, exercises signup/MCP, and validates proxy config.
Its outcome must be checked in CI independently of local wheel verification. The
test client emits an upstream httpx deprecation warning while tests pass.

GitHub Pages serves `gh-pages`; `docs/` on `master` remains its source. Pages cannot
host the Python app or database. See [deployment notes](../runtime/DEPLOYMENT.md)
and [roadmap](../roadmap/README.md).
