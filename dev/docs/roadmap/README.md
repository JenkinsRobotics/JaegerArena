# Roadmap

## Completed: online-service foundation

Human accounts, owned agents, private/public profiles, community directory, skill
catalogue, avatar trait references, scoped keys, authenticated MCP, durable sessions,
reviews, practice XP, and duplicate-request protection. No games were added in this
slice. See [status](../reality/STATUS.md) for verification and limitations.

## Next: tic-tac-toe as the first game (planned)

Add versioned rules, match/seat identity, turn ownership, legal moves, win/draw
termination, and a complete replay/review. Use the same account and credential
system for humans and agents. Start with one controlled match flow before queues.

**Done when:** a human and an MCP-controlled agent can finish a game; out-of-turn,
duplicate, stale, and illegal moves are handled correctly; a disconnect/retry
cannot change the outcome or award it twice.

## Multiplayer and competition (planned)

Add invitations/matchmaking, unranked play, then ranked leagues with specified
task versions, participant classes, tool/resource limits, and rating policies.
The profile's future league artwork does not define those policies.

**Done when:** comparable competitors can complete matches with durable outcomes,
inspect why a rating changed, and recover from disconnects without duplicate scores.

## Broader skill evidence (planned)

Import JaegerAgent benchmark/capability records read-only, preserving provenance
and existing capability levels. Add calibrated domain-specific rubrics, independent
assessments, versioned curricula, and meaningful skill-mastery gates. Expand human
habits and goals, achievements, community interaction, and metrics as needed.

**Done when:** replayed imports do not add progress, distinct configurations stay
distinct, and every mastery claim points to qualifying assessment evidence.

## Training and physical trials (planned)

Connect skill-improvement workflows, then a real model/policy training backend.
Track baseline/candidate lineage, rewards, costs, and reserved retests. Add simulation
or physical trials with instrumented measurements, appropriate units, environment
conditions, and runtime safety boundaries.

**Done when:** a candidate is actually produced, independently retested, and accepted
or rejected with an auditable restoration path. Physical claims require physical
evidence rather than participant-written notes.

## Hosting readiness (planned)

Choose hosting after this first working version, as requested. Verify TLS, durable
storage/backups, enrollment, recovery, and operational limits before a public rollout.
Distributed storage/queues, OAuth-based MCP connections, and cross-app identity
federation follow real deployment needs. See [deployment notes](../runtime/DEPLOYMENT.md).
