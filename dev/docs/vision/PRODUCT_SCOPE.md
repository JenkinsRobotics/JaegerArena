# Jaeger Arena product scope

**Train. Compete. Grow.**

Arena is a standalone app for testing, scoring, training, and improving agents,
with human participation and growth tracking in the same product. It is intended
to provide consistent evaluation and progression across the Jaeger ecosystem.
The application behavior below is **planned**.

## Participants and progression (planned)

A participant is a human or a persistent agent instance. An avatar pack supplies
appearance and character presentation, not the participant's earned capabilities.
An agent's assessment is tied to a particular model, prompt, skill, tool, and
runtime configuration. Changing those inputs creates a new evaluated version;
past results remain in history but do not automatically certify its replacement.

Agent participants practice skills, enter challenges, receive feedback, and run
training campaigns. Human participants can build skills, track habits, complete
quests, and take assessments. Self-reported habits remain distinguished from
verified assessments. A shared framework does not make a human and an agent's
scores interchangeable: direct comparison requires equivalent tests and conditions.

Track four separate things:

- **XP:** practice and participation, with repeat-award rules.
- **Mastery:** demonstrated performance on independent, versioned assessments.
- **Achievements:** specific milestones with clear evidence requirements.
- **Metrics:** task success, quality, latency, resource use, cost, and other
  domain-specific measurements with units and provenance.

## The improvement loop (planned)

1. Choose a versioned challenge, environment, rubric, and resource budget.
2. Record the participant's configuration and baseline performance.
3. Run an attempt and retain outputs, tool traces, outcomes, and errors.
4. Score with an evaluator the participant cannot rewrite during that attempt.
5. Use feedback to select practice or training; record what the training changed.
6. Evaluate the candidate against reserved assessment tasks and regression gates.
7. Promote only when the policy is met; otherwise keep the accepted version and
   record why the candidate was rejected. Retain a path to restore prior versions.

Competition uses the same evidence model. A leaderboard identifies its task set,
rubric version, tools, resource limits, and scoring conditions. Results outside
those conditions remain useful history but are not ranked as equivalent runs.

## Boundaries

Arena owns evaluation orchestration, evidence, training campaigns, and progression
presentation. It integrates with execution and training backends. It does not
reimplement JaegerAgent, define avatar packs, render avatars, own a chatbot product,
or control physical hardware outside the runtime's capability and safety boundaries.

Reinforcement learning is a training integration, not a label for XP awards.
Human habit tracking, skill/prompt optimization, and model/policy updates can share
an app while retaining distinct methods and claims.

## First useful release (planned)

Start with one local agent and one coding skill: capture an existing benchmark,
show its evidence, produce a skill revision through an existing training path,
retest independently, and record a promotion or rejection. The result must survive
restart and repeated imports must not award extra progress. Expand to multi-agent
competition, broader training backends, and human growth tracks after this loop
works end to end.
