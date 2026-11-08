# Roadmap

All application milestones below are **planned**. The completed documentation/site
foundation is recorded in [status](../reality/STATUS.md).

## 1. One participant, one skill, one evidence trail

Build a local Arena app with participant/configuration identity, read-only
JaegerAgent benchmark import, and a skill detail view. Display source capability
levels without recalculating them. Store evidence and history durably.

**Done when:** a real benchmark's score, source, skill revision, and artifacts are
inspectable after restart; reimporting it produces no extra attempt or XP; missing
provenance and failed runs are visible rather than silently ranked.

## 2. Complete the improvement loop

Add versioned challenges and rubrics, controlled execution, independent assessments,
candidate revisions through an existing skill-improvement path, and promotion or
rejection decisions. Establish the authoritative writer for every progression field.

**Done when:** one coding skill goes from baseline to candidate to reserved retest;
the app shows what changed and why it was accepted or rejected. A regression keeps
the previous accepted version available. Cancellation and resource limits work.

## 3. Competition and progression

Add practice XP, achievements, skill trees, and leaderboards restricted to equivalent
task/rubric/tool/budget conditions. Keep participation separate from mastery.

**Done when:** agents can enter comparable runs, inspect ranking evidence, and
identify incompatible results; retries cannot repeatedly award the same completion.

## 4. Reinforcement-learning campaigns

Connect a backend that consumes experience/rewards and produces a changed policy
or model checkpoint. Track the backend, training inputs, budget, and candidate lineage.

**Done when:** a real training job creates a candidate, an independent retest measures
it against the baseline, and the decision and restoration path are reproducible.
Skill/prompt optimization remains labeled separately from model training.

## 5. Humans, avatars, and wider domains

Add human quests and habits, appropriate human assessments, JaegerAvatar participant
or coach presentation, and JaegerAI capability consumers. Expand to simulation or
robot challenges only through the runtime's existing capability boundaries.

**Done when:** appearance changes preserve the participant's progress, self-reported
activity is clearly distinguished from assessed skill, and human/agent comparisons
are made only under equivalent conditions.
