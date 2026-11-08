# Jaeger Arena website

The public project site is intended to live at
[jenkinsrobotics.github.io/JaegerArena](https://jenkinsrobotics.github.io/JaegerArena/).
It explains the product and includes an illustrative six-step training-loop
explorer. It does not run agents, store learner progress, or train models.

## Source and local preview

`docs/` on `master` is the source of truth. `index.html`, `assets/site.css`,
`assets/site.js`, and local images under `assets/brand/` form a dependency-free
static site. The supplied Jaeger Arena artwork is the hero and README logo; a
compact helmet/A derivative is used in navigation and browser icons. See
[brand asset notes](BRAND.md) for provenance and source handling. The palette
retains the dark/blue identity. No external fonts, analytics, or media are
loaded. `.nojekyll` allows direct static serving.

From the repository root:

```bash
python3 scripts/check_site.py
node --check docs/assets/site.js
python3 -m http.server 8892 --bind 127.0.0.1 --directory docs
```

Open [the preview](http://127.0.0.1:8892/). Walk all six steps by mouse and keyboard,
check narrow and wide layouts, and verify that content remains readable with
JavaScript disabled and with reduced motion enabled. No npm installation is needed.

## Publishing route

This repository already has a `gh-pages` branch initialized for the website.
Preserve it: GitHub Pages should serve **`gh-pages` / `/ (root)`** using
**Deploy from a branch**. The template's conflicting `/docs` and `/gh-pages`
folder instructions have been replaced by this single route.

After checks pass and source changes are committed, update `gh-pages` with the
contents of `docs/` (including `.nojekyll`) and push that branch. Use a separate
worktree so publication does not disturb the application checkout. If files are
removed from `docs/`, remove the corresponding published copies too. Keep any
intentional hosting configuration rather than blindly replacing the entire branch.

GitHub's Pages build then publishes that branch. Pushing `master` alone does not
synchronize `gh-pages`; CI validates source but does not deploy it. Verify the
Pages workflow and served site after each publication. See
[GitHub's publishing-source guide](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
for the branch/folder setting and build troubleshooting.

## Content maintenance

The local account/profile/MCP foundation is implemented; games, public backend
hosting, and training remain planned. Preserve the illustrative label on the
website explorer and keep it distinct from the real application. Update the README
and `dev/docs/reality/STATUS.md` when runtime features ship. Link to documents on GitHub rather than
relative paths outside the published directory. Keep local assets relative so
the site works beneath `/JaegerArena/` as well as at a local server root.

## 0.1 signup and cards

The Get started section links human and agent onboarding instructions. Until an
actual shared host is verified, it states that public signup is awaiting hosting.
The card gallery illustrates empty participant records; it never queries the
private application API or presents test accounts as real community activity.
After deployment, update that section with the verified HTTPS app origin and
check its human and MCP enrollment flows before advertising public signup.
