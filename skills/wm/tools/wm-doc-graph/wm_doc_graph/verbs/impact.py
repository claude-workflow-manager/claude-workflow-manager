"""`impact <files...> [--mode=light|deep]` verb — four-dimensional impact scan.

Produces output matching the shapes in `skills/wm/references/impact-scan.md`
so existing workflow files can swap inline Grep-based impact scans for a
graph query without changing report structure. Per FIN-005 the graph stays
structural-only — FIN data is joined here at query time by parsing every
`projects/*/DECISIONS.md` under cwd.
"""

from __future__ import annotations

import re
from pathlib import Path

from ._common import (
    build_inverse_index,
    load_current_graph,
    validate_in_repo,
)


# FIN entry heading. Matches `### FIN-NNN — title`, `### FIN-NNN: title`,
# or `### FIN-NNN - title` so the parser is tolerant of minor dash/colon
# variations across projects.
_FIN_HEADING = re.compile(
    r"^###\s+FIN-(\d+)\s*[—:\-]\s*(.+?)\s*$",
    re.MULTILINE,
)


def _discover_fin_files(root: Path) -> list[Path]:
    """Find every projects/*/DECISIONS.md under root."""
    projects_dir = root / "projects"
    if not projects_dir.is_dir():
        return []
    return sorted(projects_dir.glob("*/DECISIONS.md"))


def _parse_fins(decisions_path: Path) -> list[dict]:
    """Parse FIN entries from a DECISIONS.md file.

    Returns a list of ``{id, title, body, project}`` dicts where ``body``
    is the raw text between this heading and the next FIN heading (or EOF).
    """
    try:
        text = decisions_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    project = decisions_path.parent.name
    matches = list(_FIN_HEADING.finditer(text))
    fins: list[dict] = []
    for i, m in enumerate(matches):
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        fins.append(
            {
                "id": f"FIN-{m.group(1)}",
                "title": m.group(2).strip(),
                "body": text[body_start:body_end],
                "project": project,
            }
        )
    return fins


def _fins_touching(touched_files: list[str], all_fins: list[dict]) -> list[dict]:
    """Filter FINs whose body mentions any of the touched files.

    Matches on full rel path and bare basename only — not on file stems —
    to keep false positives rare. A FIN that mentions "plan" shouldn't match
    every plan-related file; the user wants "plan.md" or the rel path.
    """
    tokens: set[str] = set()
    for f in touched_files:
        tokens.add(f)
        tokens.add(f.rsplit("/", 1)[-1])

    hits: list[dict] = []
    for fin in all_fins:
        body_lower = fin["body"].lower()
        matched = sorted(t for t in tokens if t.lower() in body_lower)
        if matched:
            hits.append({**fin, "matched": matched})
    return hits


def _downstream(
    touched_rels: list[str], inverse: dict[str, list[dict]]
) -> dict[str, list[dict]]:
    """Find downstream consumers for each touched file via the inverse index.

    Uses the same exact/suffix/basename matching as the refs verb to cope
    with un-canonicalized target strings.
    """
    result: dict[str, list[dict]] = {}
    for rel in touched_rels:
        basename = rel.rsplit("/", 1)[-1]
        matches: list[dict] = []
        seen: set = set()
        for target, records in inverse.items():
            if target == rel or target.endswith("/" + rel):
                pass
            elif target == basename or target.endswith("/" + basename):
                pass
            else:
                continue
            for r in records:
                key = (r["source"], r.get("line"), r.get("kind"))
                if key in seen:
                    continue
                seen.add(key)
                matches.append(r)
        matches.sort(key=lambda r: (r["source"], r.get("line") or 0))
        result[rel] = matches
    return result


def _plan_drift(touched_rels: list[str], root: Path) -> list[dict]:
    """Grep project plan files for mentions of touched files.

    Heuristic — "plan mentions the file" is not the same as "plan covers
    the file", but for v2.1 light touch it surfaces the candidates a
    reviewer should double-check. Deep-mode interpretation is the caller's
    responsibility.
    """
    projects_dir = root / "projects"
    if not projects_dir.is_dir():
        return []

    results: list[dict] = []
    for plan_file in sorted(projects_dir.glob("*/plans/*.md")):
        try:
            content = plan_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        matched = [
            rel
            for rel in touched_rels
            if rel in content or rel.rsplit("/", 1)[-1] in content
        ]
        if matched:
            results.append(
                {
                    "path": plan_file.relative_to(root).as_posix(),
                    "project": plan_file.parent.parent.name,
                    "matched_files": matched,
                }
            )
    return results


def _verdict(
    fin_hits: list[dict], downstream: dict[str, list[dict]], plan_hits: list[dict]
) -> str:
    total_refs = sum(len(v) for v in downstream.values())
    if fin_hits or total_refs > 5 or plan_hits:
        return "review needed"
    return "clean"


def _print_light(
    subject: str,
    touched: list[str],
    fin_hits: list[dict],
    downstream: dict[str, list[dict]],
    plan_hits: list[dict],
) -> None:
    print(f"## Impact Scan (light) — {subject}")
    print()
    print(f"Touched (declared): {', '.join(touched)}")

    if fin_hits:
        fin_list = ", ".join(f"{f['id']} ({f['project']})" for f in fin_hits)
    else:
        fin_list = "none found"
    print(f"FIN affected: {fin_list}")

    total_refs = sum(len(v) for v in downstream.values())
    if total_refs > 0:
        per_file = "; ".join(
            f"{r.rsplit('/', 1)[-1]} <- {len(downstream[r])}"
            for r in downstream
            if downstream[r]
        )
        print(f"Downstream references: {total_refs} total ({per_file})")
    else:
        print("Downstream references: none")

    if plan_hits:
        plan_list = "; ".join(
            f"{p['project']}/{p['path'].rsplit('/', 1)[-1]}" for p in plan_hits
        )
        print(f"Plan/design drift: {len(plan_hits)} plan(s) mention touched files ({plan_list})")
    else:
        print("Plan/design drift: none")

    print()
    print(f"Verdict: {_verdict(fin_hits, downstream, plan_hits)}")
    print(
        f"Reason: {len(fin_hits)} FIN(s), {total_refs} downstream ref(s), "
        f"{len(plan_hits)} plan mention(s)"
    )


def _print_deep(
    subject: str,
    touched: list[str],
    fin_hits: list[dict],
    downstream: dict[str, list[dict]],
    plan_hits: list[dict],
) -> None:
    print(f"## Impact Scan (deep) — {subject}")
    print()

    print("### Files touched")
    for f in touched:
        print(f"- {f} — (declared as input)")
    print()

    print("### FIN affected")
    print("| FIN | Project | Title | Matched tokens |")
    print("|---|---|---|---|")
    if fin_hits:
        for f in fin_hits:
            tokens = ", ".join(f["matched"])
            title = f["title"][:60]
            print(f"| {f['id']} | {f['project']} | {title} | {tokens} |")
    else:
        print("| (none) | | | |")
    print()

    print("### Downstream consumers")
    print("| Touched file | Consumer | Line | Kind |")
    print("|---|---|---|---|")
    any_rows = False
    for touched_file, refs in downstream.items():
        for ref in refs:
            line = ref.get("line") or "?"
            kind = ref.get("kind") or "?"
            print(f"| {touched_file} | {ref['source']} | {line} | {kind} |")
            any_rows = True
    if not any_rows:
        print("| (none) | | | |")
    print()

    print("### Plan / design drift")
    if plan_hits:
        for p in plan_hits:
            print(
                f"- {p['path']} (project {p['project']}) mentions: "
                f"{', '.join(p['matched_files'])}"
            )
    else:
        print("- none — no active plan mentions the touched files")
    print()

    print("### Verdict")
    print(_verdict(fin_hits, downstream, plan_hits))
    print()

    print("### Recommended action")
    total_refs = sum(len(v) for v in downstream.values())
    if not fin_hits and total_refs == 0 and not plan_hits:
        print("proceed — graph shows no structural impact")
    elif fin_hits:
        print(
            f"review {len(fin_hits)} FIN(s) before applying — they may need amendment"
        )
    elif total_refs > 0:
        print("review downstream consumers for breakage before applying")
    else:
        print("check plan mentions to confirm the change is in scope")


def run(args) -> int:
    root = Path.cwd()

    touched: list[str] = []
    for f in args.files:
        touched.append(validate_in_repo(f, root))

    graph = load_current_graph(root)

    fin_files = _discover_fin_files(root)
    all_fins: list[dict] = []
    for df in fin_files:
        all_fins.extend(_parse_fins(df))

    fin_hits = _fins_touching(touched, all_fins)

    inverse = build_inverse_index(graph)
    downstream = _downstream(touched, inverse)

    plan_hits = _plan_drift(touched, root)

    subject = ", ".join(touched)
    if args.mode == "deep":
        _print_deep(subject, touched, fin_hits, downstream, plan_hits)
    else:
        _print_light(subject, touched, fin_hits, downstream, plan_hits)

    return 0
