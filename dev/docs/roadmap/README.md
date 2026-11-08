# Roadmap

## Completed: online-service foundation

Human accounts, owned agents, private/public profiles, community directory, skill
catalogue, avatar trait references, scoped keys, authenticated MCP, durable sessions,
reviews, practice XP, and duplicate-request protection. No games were added in this
slice. See [status](../reality/STATUS.md) for verification and limitations.

## Completed: world discovery (0.2.1)

Six world groups, challenge membership and intended skill links, a browser catalog,
and shared REST/MCP discovery. The Commons has practice adapters; the five domain
worlds have planned challenges and boss concepts only. See the
[world/progression model](../vision/WORLDS_AND_PROGRESSION.md).

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

## First mastery path and boss (planned)

Build one Strategy Hall curriculum: practice, varied opponents, then a reserved
boss assessment. Add versioned eligibility rules, mastery-tier caps, qualified
stages, and clear reasons for unavailable stages. Practice XP remains independent.

**Done when:** a tier advances only from qualifying evidence; retries cannot
re-award or bypass the gate, failed assessments explain the next practice step,
and a changed agent configuration does not inherit unverified qualification.

## Broader skill evidence (planned)

Import JaegerAgent benchmark/capability records read-only, preserving provenance
and existing capability levels. Add calibrated domain-specific rubrics, independent
assessments, versioned curricula, and meaningful skill-mastery gates. Expand human
habits and goals, achievements, community interaction, and metrics as needed.

**Done when:** replayed imports do not add progress, distinct configurations stay
distinct, and every mastery claim points to qualifying assessment evidence.

## Performance and simulation worlds (planned)

Add Performance Stage evaluations for singing/rhythm and planned Lyra feedback,
with reconstruction and independent generation evaluated separately. Add locomotion
and driving through versioned simulators, bodies, and environments. Physical
qualification stays distinct from simulated scores and game unlocks.

**Done when:** recordings or simulation artifacts support domain-specific metrics,
comparisons use fixed conditions, and task failures remain visible in reviews.

## Training and physical trials (planned)

Connect skill-improvement workflows, then real model/policy training backends.
Track evolutionary candidate search and reinforcement learning as distinct methods.
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
