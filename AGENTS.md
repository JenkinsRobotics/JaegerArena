# Working on Jaeger Arena

Read these before making changes:

1. `dev/docs/reality/STATUS.md` — implemented behavior and verification limits.
2. `dev/docs/vision/PRODUCT_SCOPE.md` — product boundaries.
3. `dev/docs/vision/ARCHITECTURE.md` and `INTEGRATIONS.md` — intended ownership.
4. `CONVENTIONS.md` — ecosystem conventions.

Arena is the evaluation and training product. It does not own the agent engine,
avatar pack format, avatar renderer, or hardware safety layer. Reuse upstream
benchmark and capability machinery; do not duplicate level calculations in the UI.

Keep planned behavior explicitly labeled. Practice XP, earned mastery, and model
training are different concepts. Progress belongs to the participant; evidence
must identify the evaluated configuration. Never describe demo numbers as live
results or imply an assessment guarantees general intelligence.

`docs/` is the website source. The repository has an existing `gh-pages` publishing
branch; preserve that route unless the user requests a change. The site has no
build dependencies. Keep its assets local, links project-path compatible,
interactions keyboard accessible, and content visible without JavaScript.

`dev/template-reference/` is inactive source material, not application code.
Do not activate its module or hardware examples to fabricate an Arena runtime.

The runtime lives in `jaeger_arena/`. REST and MCP must use the same service-level
ownership and award rules. Runtime data belongs in ignored `.arena/` or `.local/`;
never commit a database, password, session cookie, or credential value. Participant
credentials may not grade attempts. Keep character traits separate from earned
evidence, practice XP separate from competitive rank, and unimplemented games
explicitly unavailable. Run `.venv/bin/python -m pytest -q` for runtime changes.

For documentation/site changes run `python3 scripts/check_site.py` and
`git diff --check`. Walk changed interactions in a browser and check narrow and
wide layouts. Update `dev/docs/reality/STATUS.md` when behavior or verification
changes. Runtime work will need checks appropriate to the implementation.
