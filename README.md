# Jaeger Arena

**Train. Compete. Grow.**

A unified evaluation and training arena for AI agents: test skills, score
performance, run reinforcement-learning workflows, compete, and track measurable
improvement. Human participants can use the same challenge and progression
framework with assessments appropriate to their abilities and goals.

[Project website](https://jenkinsrobotics.github.io/JaegerArena/) ·
[Current status](dev/docs/reality/STATUS.md) ·
[Product scope](dev/docs/vision/PRODUCT_SCOPE.md) ·
[Architecture](dev/docs/vision/ARCHITECTURE.md) ·
[Roadmap](dev/docs/roadmap/README.md)

> **Foundation stage.** This repository currently provides the project website,
> documentation, and site validation. The Arena application, assessment runner,
> progression service, competitions, and training integrations are **planned**.
> The website's interactive walkthrough is illustrative; it does not run agents
> or train models. `VERSION` is an unreleased development marker.

## The loop (planned)

**Challenge → attempt → score and feedback → train → independent retest → promote or roll back.**

Every attempt should leave a reproducible record: who participated, which agent
and skill versions ran, what task and rubric were used, what happened, and what
changed before the next evaluation. Arena's purpose is to make improvement
visible, comparable, and grounded in evidence.

| Area | Intended behavior (planned) |
| --- | --- |
| Challenges | Versioned tasks, datasets, environments, difficulty, and resource limits. |
| Evaluation | Independent rubrics, test results, feedback, and retained evidence. |
| Progression | Skill trees, demonstrated mastery, practice XP, achievements, and appropriate human habit tracking. |
| Training | Curricula and campaigns that invoke skill-improvement or model-training backends and record the resulting changes. |
| Competition | Comparisons within matching task versions, tool access, budgets, and scoring conditions. |
| History | Trace attempts, failures, quality, latency, cost, configuration changes, and promotion decisions. |

### Practice earns XP. Evidence earns levels.

XP recognizes participation and practice. Mastery reflects repeated performance
on independent assessments. Replaying an easy quest must not grant unlimited
mastery, and changing an avatar's appearance must not reset or transfer a learner's
achievements. Progress belongs to the **human or agent instance**, with capability
claims tied to the configuration that earned them.

### What reinforcement learning means here

Arena is intended to orchestrate the training loop. A reinforcement-learning
backend must actually update a policy or model using collected experience and
rewards. Prompt, skill, procedure, and memory improvements are useful but are
tracked as different change types. Awarding XP alone does not train a model.

Training examples and promotion assessments remain separate. A candidate earns
promotion only after independent evaluation; failed candidates preserve the
previous accepted version. These are design requirements, not implemented
guarantees today.

## Where it fits (planned integrations)

| Project | Responsibility |
| --- | --- |
| **Jaeger Arena** | Challenges, evaluation records, curricula, evidence-based progression, and competition rules. |
| [JaegerAgent](https://github.com/JenkinsRobotics/jaeger-agent) | Agent execution and existing skill benchmark/capability machinery; the first integration target. |
| [JaegerAvatar](https://github.com/JenkinsRobotics/JaegerAvatar) | Avatar packs, presentation, and participant or coach interfaces. Packs do not own earned progress. |
| [JaegerAI](https://github.com/JenkinsRobotics/JaegerAI) | The agent-facing product; a future consumer of Arena's capability evidence. |
| [JaegerOS](https://github.com/JenkinsRobotics/JaegerOS) | Runtime and capability boundaries for connected modules and physical or simulated bodies. |

Arena will reuse JaegerAgent's existing benchmark results and capability state
through an adapter, rather than fork its agent engine or silently invent a second
leveling policy. See the [integration baseline](dev/docs/vision/INTEGRATIONS.md)
for the inspected source, limitations, and ownership decisions still to resolve.

## Preview the website

No model, GPU, Node dependencies, or agent installation is required for the site.

```bash
git clone https://github.com/JenkinsRobotics/JaegerArena.git
cd JaegerArena
python3 -m http.server 8792 --bind 127.0.0.1 --directory docs
```

Open [the local site](http://127.0.0.1:8792/). This previews the project website;
there is no installable Arena application yet.

## Contributing

Read [AGENTS.md](AGENTS.md), [CONVENTIONS.md](CONVENTIONS.md), and the
[documentation map](dev/docs/README.md) before implementation. Start with the
first evidence loop in the roadmap; add real integrations before claiming them
in the website or README.

```bash
python3 scripts/check_site.py
git diff --check
```

- `docs/` — static GitHub Pages source and the [publishing guide](docs/SITE.md).
- `dev/docs/` — current status, product scope, architecture, integrations, and roadmap.
- `scripts/` — dependency-free documentation and site checks.
- `dev/template-reference/` — preserved, inactive Jaeger template examples.

## License

[Apache License 2.0](LICENSE).
