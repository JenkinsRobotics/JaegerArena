# Current status — 2026-11-08

**Jaeger Arena is in its foundation stage. No Arena application or model-training
backend is implemented in this repository.** `VERSION` is an unreleased development
marker, not an installable application release.

## Implemented

- README, product scope, intended architecture, integration baseline, and an ordered
  roadmap with acceptance criteria.
- Static project website in `docs/`, with a six-step interactive concept walkthrough,
  progression explanation, ecosystem map, and roadmap. All walkthrough records
  are illustrative and do not execute real work.
- Dependency-free site/documentation checks and CI that fails on validation errors.
- Original module/workspace examples retained as inactive `dev/template-reference/`
  material. They are not an Arena runtime or dependency pin.

## Existing elsewhere; not integrated here

JaegerAgent provides skill benchmarking, benchmark history, and per-capability state
with promotion/demotion machinery. Source inspection informed the planned adapter;
Arena does not yet import those records or control agent execution. Avatar packs
and rendering remain owned by JaegerAvatar.

## Planned

Participant/configuration records, durable evidence storage, challenge execution,
independent evaluators, XP/mastery services, training adapters, competitions,
Jaeger ecosystem integrations, and human growth tracks. There are no application
install/run commands or finalized public API schemas yet.

## Verification

Completed locally on 2026-11-08:

- `python3 scripts/check_site.py`: local/repository links, metadata, unique HTML
  IDs, image alternative text, and active-document template placeholders passed.
- `node --check docs/assets/site.js` and `git diff --check` passed.
- Chromium walkthrough: all six explorer steps, keyboard selection and wrapping,
  section navigation, JavaScript-disabled fallback, and reduced-motion mode passed.
- Layouts at 320, 390, 768, 1024, and 1440 pixels had no horizontal overflow;
  desktop and mobile screenshots were visually reviewed. No browser script or
  resource errors were reported. This is not a full accessibility audit.

The existing GitHub Pages publishing route uses `gh-pages`; source lives in `docs/`
on `master`. See [site guide](../../../docs/SITE.md). CI validates source and does
not synchronize the publishing branch. No agent execution, learning, persistent
progress, or live integration is claimed by these website checks.
