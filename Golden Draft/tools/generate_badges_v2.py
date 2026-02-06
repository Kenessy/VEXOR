#!/usr/bin/env python3
"""
VRAXION Badge Generator (v2, unified glass style)

Generates SVG label badges from:
  - docs/assets/badges/_templates/glass_template.svg
  - docs/assets/badges/_templates/badges_v2.json

Outputs:
  - docs/assets/badges/v2/*.svg   (canonical)
  - docs/assets/badges/mono/*.svg (compat copy; byte-identical)
  - docs/assets/badges/neon/*.svg (compat copy; byte-identical)

Stdlib-only by design (runs in CI).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path


_TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


@dataclass(frozen=True)
class BadgeSpec:
    badge_id: str
    text: str
    accent: str
    kind: str  # "badge" | "chip"


def _escape_xml_text(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _measure_badge_width(label: str) -> int:
    # A pragmatic estimate that reads well across GitHub/Wiki/PAGES renders.
    # left padding starts after the optional rail; label starts at x=14.
    base = 14 + 12
    per_char = 7.0
    spacing = 0.6
    n = len(label)
    w = base + (n * per_char) + (max(0, n - 1) * spacing)
    return max(44, int(math.ceil(w)))


def _measure_chip_width(_label: str) -> int:
    return 44


def _render_svg(template: str, spec: BadgeSpec) -> str:
    label = _escape_xml_text(spec.text)

    if spec.kind == "chip":
        w = _measure_chip_width(label)
        rail_block = ""
        text_anchor = "middle"
        text_x = f"{w/2:g}"
        letter_spacing = "0.7"
        font_weight = "900"
    else:
        w = _measure_badge_width(label)
        rail_block = (
            f'<rect x="2" y="2" width="5" height="20" rx="2" '
            f'fill="{spec.accent}" fill-opacity="0.90"/>'
        )
        text_anchor = "start"
        text_x = "14"
        letter_spacing = "0.7"
        font_weight = "900"

    values: dict[str, str] = {
        "W": str(w),
        "INNER_W": str(w - 1),
        "HLINE_END": f"{w - 2.5:g}",
        "ID": spec.badge_id,
        "LABEL": label,
        "ACCENT": spec.accent,
        "RAIL_BLOCK": rail_block,
        "TEXT_X": text_x,
        "TEXT_ANCHOR": text_anchor,
        "LETTER_SPACING": letter_spacing,
        "FONT_WEIGHT": font_weight,
    }

    missing: set[str] = set()

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            missing.add(key)
            return match.group(0)
        return values[key]

    out = _TOKEN_RE.sub(_sub, template)
    if missing:
        raise RuntimeError(f"Template placeholders missing values: {sorted(missing)}")
    if not out.endswith("\n"):
        out += "\n"
    return out


def _load_manifest(path: Path) -> list[BadgeSpec]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    badges = raw.get("badges")
    if not isinstance(badges, list) or (not badges):
        raise RuntimeError("badges_v2.json: expected non-empty 'badges' list")

    specs: list[BadgeSpec] = []
    seen: set[str] = set()
    for b in badges:
        if not isinstance(b, dict):
            raise RuntimeError("badges_v2.json: each badge must be an object")
        badge_id = str(b.get("id", "")).strip()
        text = str(b.get("text", "")).strip()
        accent = str(b.get("accent", "")).strip()
        kind = str(b.get("kind", "")).strip().lower()

        if not badge_id or (not re.fullmatch(r"[a-z0-9_]+", badge_id)):
            raise RuntimeError(f"badges_v2.json: invalid id: {badge_id!r}")
        if badge_id in seen:
            raise RuntimeError(f"badges_v2.json: duplicate id: {badge_id}")
        if not text:
            raise RuntimeError(f"badges_v2.json: missing text for id: {badge_id}")
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", accent):
            raise RuntimeError(f"badges_v2.json: invalid accent for id {badge_id}: {accent!r}")
        if kind not in ("badge", "chip"):
            raise RuntimeError(f"badges_v2.json: invalid kind for id {badge_id}: {kind!r}")

        seen.add(badge_id)
        specs.append(BadgeSpec(badge_id=badge_id, text=text, accent=accent, kind=kind))

    return specs


def _dir_svg_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {p.stem for p in path.glob("*.svg") if p.is_file()}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="generate_badges_v2.py", description="Generate VRAXION SVG badges (v2).")
    ap.add_argument("--check-only", action="store_true", help="Verify outputs are up-to-date; do not write files.")
    args = ap.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    tmpl_path = repo_root / "docs" / "assets" / "badges" / "_templates" / "glass_template.svg"
    manifest_path = repo_root / "docs" / "assets" / "badges" / "_templates" / "badges_v2.json"

    out_v2 = repo_root / "docs" / "assets" / "badges" / "v2"
    out_mono = repo_root / "docs" / "assets" / "badges" / "mono"
    out_neon = repo_root / "docs" / "assets" / "badges" / "neon"

    if not tmpl_path.exists():
        print(f"ERROR: missing template: {tmpl_path}")
        return 2
    if not manifest_path.exists():
        print(f"ERROR: missing manifest: {manifest_path}")
        return 2

    template = tmpl_path.read_text(encoding="utf-8", errors="replace")
    specs = _load_manifest(manifest_path)

    expected_ids = {s.badge_id for s in specs}
    issues: list[str] = []

    if not args.check_only:
        out_v2.mkdir(parents=True, exist_ok=True)
        out_mono.mkdir(parents=True, exist_ok=True)
        out_neon.mkdir(parents=True, exist_ok=True)

    # Render v2 files
    for spec in specs:
        try:
            svg = _render_svg(template, spec)
        except Exception as e:  # noqa: BLE001 - want a short failure line
            issues.append(f"render_failed: {spec.badge_id}: {type(e).__name__}: {e}")
            continue

        p = out_v2 / f"{spec.badge_id}.svg"
        if args.check_only:
            if not p.exists():
                issues.append(f"missing_v2: {p}")
            else:
                existing = p.read_text(encoding="utf-8", errors="replace")
                if existing.replace("\r\n", "\n") != svg.replace("\r\n", "\n"):
                    issues.append(f"stale_v2: {p}")
        else:
            p.write_text(svg, encoding="utf-8", newline="\n")

    # Enforce no extras in v2 (check-only)
    if args.check_only and out_v2.exists():
        extra_v2 = _dir_svg_ids(out_v2) - expected_ids
        if extra_v2:
            issues.append(f"extra_v2_files: {sorted(extra_v2)}")

    # Copy v2 -> mono/neon (or verify copies)
    for compat_dir in (out_mono, out_neon):
        if args.check_only and (not compat_dir.exists()):
            issues.append(f"missing_compat_dir: {compat_dir}")
            continue

        compat_ids = _dir_svg_ids(compat_dir)
        if args.check_only:
            extra = compat_ids - expected_ids
            if extra:
                issues.append(f"extra_compat_files: {compat_dir}: {sorted(extra)}")

        for badge_id in sorted(expected_ids):
            src = out_v2 / f"{badge_id}.svg"
            dst = compat_dir / f"{badge_id}.svg"

            if args.check_only:
                if not dst.exists():
                    issues.append(f"missing_compat: {dst}")
                    continue
                try:
                    if src.read_bytes() != dst.read_bytes():
                        issues.append(f"compat_mismatch: {dst} (expected byte-identical to v2)")
                except Exception as e:  # noqa: BLE001
                    issues.append(f"compat_read_failed: {dst}: {type(e).__name__}: {e}")
            else:
                dst.write_bytes(src.read_bytes())

    if issues:
        print("\nBADGE GENERATION (v2) FAILURES:")
        for i in issues:
            print(f"- {i}")
        print("\nSUMMARY:")
        print(f"- issues: {len(issues)}")
        return 1

    print("\nSUMMARY:")
    print("- issues: 0")
    print(f"- badge_ids: {len(expected_ids)}")
    print(f"- check_only: {bool(args.check_only)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

