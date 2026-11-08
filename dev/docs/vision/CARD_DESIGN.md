# Participant cards

The additional user-supplied references guide the hierarchy and density of Arena's
cards: strong participant identity, compact stat groups, segmented progression,
readable activity rows, and distinct treatment for competition. Keep the existing
cyan Arena identity; use gold within the competition card. No reference artwork,
commercial copy, health recommendations, or sample player statistics are copied.

## Implemented card treatment

- **Participant:** persistent human/agent identity, chosen avatar reference,
  membership month, visibility, bio, and actual Unranked status.
- **Practice progression:** the server's practice level, XP, next-level threshold,
  and progress ratio. The segmented bar is presentation only; the browser does
  not invent a level policy.
- **Stat group:** completed sessions, skills with reviewed evidence, pending
  reviews, and achievements, taken from the existing profile response.
- **Learning activity:** reviewed skill-attempt counts by domain. Counts include
  all recorded configurations/rubrics; the card explicitly does not infer mastery.
  Connection checks do not count as skill reviews. Empty data remains zero.
- **Next step:** a deterministic owner action based on actual records: view pending
  reviews, complete the connection check, or record skill practice. This is not an
  AI diagnosis, health recommendation, or personalized capability assessment.
- **Recent activity:** latest five sessions by start date, with status, awarded XP,
  and links to their controls/reviews. Only the owner sees this card. Public profile
  views do not fetch or render private history. “No XP” means no award on that
  session; completed repeat attempts may legitimately receive no additional XP.
- **Competition preview:** Unranked status with planned leagues, rewards, and
  standings. No fictional season dates, rank thresholds, reward unlocks, percentile,
  or leaderboard positions are presented as live data.

The app uses existing APIs and storage. No backend schema or scoring changes were
needed. Character traits remain declared attributes, separate from reviewed skills.
The public project site's card gallery uses clearly labeled empty-state examples;
it does not read real participant records.

## Planned additions inspired by the references

| Card | Requirements before it can show live values |
| --- | --- |
| Season / leaderboard | Versioned season dates, comparable competition classes, rating/XP policy, real results, and explicit reset rules. Practice XP and match rank stay distinct. |
| Rewards | Defined award conditions and authoritative unlock records. No cosmetic lock implies an available reward system today. |
| Progress trend / before-and-after | Comparable metric history, units, date range, configuration/rubric matching, and declared comparison rules. Attempt volume alone is not improvement. |
| Partner / team streak | Accepted relationships, opt-in visibility, timezone/qualifying-event policy, and actual participation. A login or browser-open event is not demonstrated skill growth. |
| Nudge / invitation | Implemented, permission-scoped delivery, rate limits, and recipient controls. The design does not send anyone a message. |
| Personal goals / class identity | A persisted participant-selected goal or character role. Do not infer a person's personality or assign a capability class from sparse activity. |

## Verification

Exercise empty and populated profiles, owner/public visibility, participant switching,
next-step actions, recent-session navigation, and narrow/wide layouts. Public views
must not request the private history API. Existing signup, review, community, and
credential flows must continue to work. No illustrative participants are seeded
into the normal application database.
