# Integration baseline

Inspected on **2026-11-08**. The Arena account/session application is implemented.
The JaegerAgent benchmark adapter below is still **planned**.

## JaegerAgent: reuse this first

The local `jaeger-agent` checkout contains:

- [`skill_benchmark.py`](https://github.com/JenkinsRobotics/jaeger-agent/blob/master/jaeger_agent/skill_registry/skill_benchmark.py):
  `benchmark_skill` runs a skill's `tests/benchmark.py` with a 120-second timeout,
  parses a JSON result, appends `tests/benchmark_history.jsonl`, and reports the
  prior score and delta. Benchmark results include `score`, `passed`, and `total`,
  with optional cases, notes, and a capability selector.
- [`capability_state.py`](https://github.com/JenkinsRobotics/jaeger-agent/blob/master/jaeger_agent/skill_registry/capability_state.py):
  per-skill `state.yaml` and `history.jsonl`, using the existing
  `jros.skill_state/v1` schema name. The current policy uses three consecutive
  qualifying results to promote and three below the current floor to demote;
  capability manifests determine the score bands.
- [Skill self-improvement pipeline](https://github.com/JenkinsRobotics/jaeger-agent/blob/master/docs/pipelines/skill_self_improvement_pipeline.md):
  describes smoke checks, benchmarking, comparison, and curator rollback.

Do not rename that external schema merely to match new branding. Preserve source
semantics and version the adapter when the upstream contract changes. The current
append path relies on callers to prevent duplicate runs; importing the same file
again must not inflate counters or progression.

The inspected benchmark/state code does not establish independent held-out
evaluation, grader integrity, reward calibration, or reliable automatic rollback
across every upstream path. Arena must verify those properties before claiming
them. Importing an existing level records its source, not proof of broader ability.

## Planned integration sequence

1. Import benchmark artifacts and capability state read-only. Preserve provenance,
   mark incomplete records, and deduplicate replayed imports.
2. Add a supported JaegerAgent execution adapter with scoped jobs and cancellation.
   Keep credential and agent lifecycle ownership in the appropriate host.
3. Introduce independent assessment, recording candidate configurations and explicit
   acceptance decisions. Reconcile progression ownership before adding a writer.
4. Invoke skill-improvement workflows, then add model/policy-training backends
   when experience and reward records can actually drive updates.
5. Expose assessed capabilities to JaegerAI and avatar presentation to JaegerAvatar.

## JaegerAvatar references (implemented)

The app snapshots 51 avatar/profile references from `avatar/v1`, with source paths
and manifest hashes. Twenty profiles have declared trait groups: HEXACO-labeled
personality fields, SPECIAL attributes, expression, and domains. The stored
HEXACO-labeled group includes upstream names unchanged; Arena does not reinterpret
it as a validated psychological assessment. No earned skill tree was found in the
inspected packs, so Arena owns its extensible skill catalogue separately.

`scripts/import_avatar_references.py` refreshes metadata only; it copies no
renderers, character prompts, avatar assets, or earned levels. Profile selection
currently reads the bundled reference snapshot; live rendering and cross-app
identity federation are not wired.

## Other ecosystem boundaries

| Project | Arena relationship |
| --- | --- |
| JaegerAvatar | Uses avatar packs to present participants and coaches. Arena stores progress separately, referenced by participant identity. |
| JaegerAI | May launch challenges or consume assessed capability information for user workflows and routing. |
| JaegerOS | Supplies the runtime/capability boundary for module and robot integrations. Hardware safety remains below Arena. |
| Aether Animation | May author rig behavior used in a future challenge. It is not an evaluation or agent-learning service. |

The training backend and cross-app identity transport are intentionally undecided.
Pin a tested upstream revision when implementing the adapter; these source links
describe the inspected baseline and are not dependency pins.
