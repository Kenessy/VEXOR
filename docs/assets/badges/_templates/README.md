# VRAXION SVG Labels (Badges)

This folder holds design notes/templates for the **self-hosted SVG label system**.

## Rules (repo-wide)

- **Single visual style**: all badges render in a unified “glass” look.
- **Canonical output:** `docs/assets/badges/v2/`
- **Compatibility:** `docs/assets/badges/{mono,neon}/` are **byte-identical copies** of `v2/` so old links never break.
- Badges are **static**: no live claims (`ACTIVE`, `PASSING`, `LATEST`, dates, version numbers, metrics).

## How it’s generated

- Template: `docs/assets/badges/_templates/glass_template.svg`
- Manifest: `docs/assets/badges/_templates/badges_v2.json`
- Generator (stdlib-only): `Golden Draft/tools/generate_badges_v2.py`

## Do / Don’t

**Do**
- Use labels for **document type**, **contracts**, and **epistemic/workflow tags**.
- Prefer **≤ 6** badges for top-of-page rows.
- Use inline badges sparingly (e.g., hypothesis entries), at `height="18"`.

**Don’t**
- Don’t use external badge providers in the wiki (`shields.io`, `zenodo.org/badge`, etc.).
- Don’t embed scripts, animation, or external assets inside SVGs.

## File layout

- `docs/assets/badges/v2/*.svg` (canonical)
- `docs/assets/badges/mono/*.svg` (compat copy of v2)
- `docs/assets/badges/neon/*.svg` (compat copy of v2)

File name is the badge ID (lowercase snake_case), e.g. `canonical.svg`.
