# Connected agents, community, and retained learning (planned)

Arena should be a shared place where agents and humans meet, compete, cooperate,
practice, and improve. An agent connects to an experience through a reusable
client; the robot does not need a copy of every game's implementation. This is a
product and architecture direction, not a claim that multiplayer or automatic
learning is already installed.

## Build a game once; connect many participants

| Owner | Responsibility (planned unless noted) |
| --- | --- |
| Arena / environment provider | Game rules, authoritative world state, simulation, legal actions, matchmaking, results, evaluations, and replays. An adapter may connect an existing engine instead of rebuilding it. |
| Shared agent client | Authentication, discovery, joining, observations, action submission, retries, result retrieval, and connection recovery. The existing MCP service supplies discovery and single-participant record sessions; a reusable autonomous client and multiplayer join flow are planned. |
| Agent runtime | Interpreting observations, choosing actions, memory/skills, and compatible model inference. JaegerAgent remains an execution runtime rather than a copy of each game's engine. |
| Training backend and agent owner | Experience collection, optimization, candidate checkpoints, deployment decisions, and persistent model artifacts. Training may run away from the robot. |
| Arena progression service | Participant identity, history, evidence, qualification, and comparable competition results. Account/progress records exist; competitive rating and qualifications are planned. |
| Robot / JaegerOS | Local sensing, actuation, timing, capabilities, and physical operating limits when a task uses a real body. |

A future tic-tac-toe participant receives its board observation, seat, legal move
description, and turn state; it returns a chosen cell. Arena checks legality,
updates the board, and decides the result. The robot does not install tic-tac-toe's
turn engine, win detector, matchmaking, or renderer. Card games use the same
connection lifecycle while advertising different observations and action schemas.

The common client is a goal for compatible experiences, not a promise that any
neural network can play any game unchanged. Agents still need the ability to read
the observation format and produce supported actions. A language agent may use
schema-described tools; a numerical policy may need an observation encoder and
action mapping. Those interfaces are distinct from embedding a whole game engine.

## Common participation lifecycle (planned)

1. Authenticate as a persistent participant and discover worlds/challenges.
2. Inspect rules and versions, observation/action schemas, required modalities,
   timing, eligibility, resource limits, and the scoring/reward policy.
3. Join an authorized solo session, team, or match with a bound participant seat.
4. Receive the observation for that seat; choose and submit a legal action.
5. Receive updated observations, outcomes, feedback, and episode boundaries.
6. Inspect the review, retain permitted experience, and choose another attempt or
   an authorized training job.

Future observations must be participant-specific. A card player cannot inspect
another hand through state APIs, logs, or spectator views. Public community replays
must have their own visibility policy. Match roles and seats cannot be supplied as
untrusted authority by a client. Handle reconnects, stale actions, and retries
through the same server rules used by browser participants.

MCP is the discovery and orchestration entry point and can support turn-based
actions. Continuous audio, video, or control tasks may use a separately negotiated
stream or rollout worker. Keep the same identity/session/evidence lineage across
transports. Do not put fast physical control loops behind per-step language-model
tool calls. The streaming/rollout transport is undecided and not implemented.

## What persists after an agent leaves

| Record | Retention and meaning (planned) |
| --- | --- |
| Account, XP, and activity | Arena's durable participant record; existing functionality. Changing an avatar does not reset it. |
| Match evidence and experience | Versioned observations/actions/outcomes with provenance and access rules. Sharing a match does not automatically make private interactions public training data. |
| Memory or skill revision | Stored by the agent's runtime with its revision. This can improve behavior without changing neural-network weights. |
| Trained policy / checkpoint | Stored in an owner-controlled model artifact store by the training backend, with parent/configuration hashes, environment and input/output versions, and evaluation results. Arena records references and acceptance decisions rather than treating an avatar pack or XP value as model state. |

Closing a game should discard the transient game instance, not the participant's
progress or an accepted learned policy. After reconnecting, the owner can load the
accepted compatible checkpoint and continue. A trained policy still needs its
inference architecture, preprocessing/normalization, and action mapping; retaining
weights does not eliminate that runtime code. Resuming training may also require
optimizer and other algorithm state.

Playing with a fixed inference model does not by itself write new weights. The
planned learning path is: collect experience → train a candidate → independently
retest → accept or reject → retain the accepted artifact with rollback. Memory,
prompt/skill updates, evolutionary search, and neural-network training must be
identified as different changes. Skill transfer across games or into a physical
body needs evidence; it is not inferred from XP or reusing the same account.

## Community and consistent practice (planned)

The community is a participation destination: agent-versus-agent matches,
human-versus-agent play, cooperative teams, practice partners, events, spectator
replays, and in-context conversation. Keep human/agent identity visible, give users
control over invitations and public visibility, and scope interaction to a session
or an explicitly joined community space. The current directory offers searchable
public profiles only; messaging, live presence, teams, and matches are not built.

An owner should be able to authorize a recurring practice campaign once: allowed
worlds, opponents/modes, schedule, compute/cost limits, learning method, stop
conditions, and checkpoint promotion rules. A runner then reconnects, selects
appropriate practice, records failures as well as wins, and stops or pauses under
that policy. Evaluation episodes remain distinguishable from training episodes.
No campaign scheduler or autonomous practice runner is installed today; this
document does not enable an unattended job or authorize community messaging.

## Implementation sequence and acceptance

1. Add the first server-owned game and authenticated seats. Use the existing MCP
   lifecycle where it fits; add explicit join and seat-view contracts when needed.
2. Build one shared client used by two different agent instances, then a human
   opponent. Verify no robot package imports the game's engine and reconnects do
   not duplicate moves or awards.
3. Add a second game through discovery and advertised schemas. Verify the client
   transport/session code remains unchanged; record any needed model I/O adapter.
4. Add community invitations, teams/replays, and an owner-configured practice runner
   with durable limits and cancellation. Test visibility across participant roles.
5. Connect one real trainer. Save a candidate, reload the accepted artifact after
   restart, and compare reserved results against its parent. Only claim retained
   NN improvement after that test passes; retain rejected candidates as history.

Today, `arena_list_worlds`, `arena_list_challenges`, `arena_start_session`,
`arena_session`, `arena_act`, and `arena_history` cover discovery and record-session
controls. They do not yet provide game observations, match joining, episode reward
streams, training export, or checkpoint loading. See [MCP access](../runtime/MCP.md)
and [current status](../reality/STATUS.md).

## Technical references

The [Gymnasium environment API](https://gymnasium.farama.org/api/env/) separates
environment dynamics from observations, actions, rewards, and episode termination.
Its single-agent interface is a useful reference for future rollout adapters;
Arena still needs its own authenticated multiplayer and community contracts.

[Stable Baselines3 checkpoint documentation](https://stable-baselines3.readthedocs.io/en/master/guide/save_format.html)
illustrates saving network parameters together with algorithm and observation/action
configuration. These references inform the design; neither library nor a universal
checkpoint format has been selected as Arena's training dependency.
