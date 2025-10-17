#!/usr/bin/env python3
"""
update_table.py — Rebuild a 3-column Submodules table for the CURRENT repo
(even when this script lives inside a tools submodule).

- Run this from the meta-repo root:
    python tools/readme-tools/update_table.py
- Reads .gitmodules in the meta-repo.
- Table: Name | Description | Preview
- Description: first meaningful line of each submodule's README.md (local).
- Preview: if submodule has img/gui.png locally AND host is GitHub/GitLab,
  uses a HEAD-based raw URL so it renders on GitHub. Otherwise shows "–".
- Replacement priority:
  1) Replace <!-- BEGIN: SUBMODULE_TABLE --> ... <!-- END: SUBMODULE_TABLE -->
  2) Else replace first table starting with "| Name"
  3) Else create/replace under a "## Submodules" section.

No network calls. Skips anything missing or unreachable without delay.
"""

from __future__ import annotations
import os, re, subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict

MARKER_BEGIN = "<!-- BEGIN: SUBMODULE_TABLE -->"
MARKER_END   = "<!-- END: SUBMODULE_TABLE -->"
IMG_RELATIVE = "img/gui.png"

def sh(args: list[str], cwd: Optional[Path] = None) -> str:
    return subprocess.check_output(args, cwd=str(cwd) if cwd else None)\
        .decode("utf-8", "replace").strip()

def repo_root_from_cwd() -> Path:
    # Determine the top-level of the repo for the CURRENT working directory
    top = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(top).resolve()

def parse_gitmodules(root: Path) -> list[dict[str, Optional[str]]]:
    gm = root / ".gitmodules"
    items: list[dict[str, Optional[str]]] = []
    if not gm.exists():
        return items
    current: dict[str, Optional[str]] = {}
    for raw in gm.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line.startswith("[submodule"):
            if current:
                items.append(current)
            current = {"path": None, "url": None, "branch": None}
        elif "=" in line:
            k, v = [s.strip() for s in line.split("=", 1)]
            if k in ("path", "url", "branch"):
                current[k] = v
    if current:
        items.append(current)
    return [x for x in items if x.get("path")]

def normalize_repo(url: str) -> Optional[dict[str, str]]:
    if not url: return None
    u = url.strip()
    if u.endswith(".git"):
        u = u[:-4]
    m = re.match(r"^git@([^:]+):([^/]+)/(.+)$", u)  # ssh
    if m:
        return {"host": m.group(1).lower(), "owner": m.group(2), "repo": m.group(3)}
    m = re.match(r"^https?://([^/]+)/([^/]+)/(.+)$", u)  # https
    if m:
        return {"host": m.group(1).lower(), "owner": m.group(2), "repo": m.group(3)}
    return None

def first_description_line(readme_path: Path) -> str:
    if not readme_path.exists():
        return "_No README found._"
    lines = readme_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return "_No description available._"
    if lines[i].lstrip().startswith("#"):
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and not lines[j].lstrip().startswith("#"):
            return lines[j].strip()
        return lines[i].lstrip("#").strip() or "_No description available._"
    return lines[i].strip()

def cell_escape(text: str) -> str:
    return text.replace("|", r"\|")

def raw_url_head(info: dict[str, str]) -> Optional[str]:
    # Only use hosts we know accept HEAD without extra lookups
    host = info["host"]
    owner = info["owner"]
    repo  = info["repo"]
    if "github.com" in host or host.endswith("github.com"):
        return f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{IMG_RELATIVE}"
    if "gitlab.com" in host:
        return f"https://gitlab.com/{owner}/{repo}/-/raw/HEAD/{IMG_RELATIVE}"
    return None  # skip for others (Bitbucket/self-hosted) to stay fast

def build_table(root: Path) -> str:
    subs = parse_gitmodules(root)
    subs = sorted(subs, key=lambda d: Path(d["path"]).name.lower())
    rows = []
    for sm in subs:
        rel_path = sm["path"]
        url      = sm.get("url") or ""
        sub_path = (root / rel_path).resolve()
        name     = sub_path.name

        name_cell = f"[{name}]({url})" if url else name
        desc      = first_description_line(sub_path / "README.md")
        desc_cell = cell_escape(desc)

        preview_cell = "–"
        img_local = sub_path / IMG_RELATIVE
        if img_local.exists() and url:
            info = normalize_repo(url)
            if info:
                raw = raw_url_head(info)
                if raw:
                    preview_cell = f'<img src="{raw}" width="140" alt="{name} GUI">'

        rows.append(f"| {name_cell} | {desc_cell} | {preview_cell} |")

    header = "| Name | Description | Preview |\n| --- | --- | :---: |"
    return "\n".join([header] + rows) if rows else (header + "\n| – | _No submodules found._ | – |")

def replace_with_markers(text: str, table_md: str) -> Optional[str]:
    if MARKER_BEGIN in text and MARKER_END in text:
        return re.sub(
            rf"{re.escape(MARKER_BEGIN)}[\s\S]*?{re.escape(MARKER_END)}",
            f"{MARKER_BEGIN}\n{table_md}\n{MARKER_END}",
            text, flags=re.MULTILINE
        )
    return None

def replace_existing_table(text: str, table_md: str) -> Optional[str]:
    pat = re.compile(r"(^\|[^\n]*Name[^\n]*\n\|[^\n]*\n(?:\|[^\n]*\n)+)", flags=re.MULTILINE)
    if pat.search(text):
        return pat.sub(table_md + "\n", text, count=1)
    return None

def ensure_submodules_section(text: str, table_md: str) -> str:
    subsec_pat = re.compile(r"^##\s+Submodules\s*$", flags=re.MULTILINE)
    m = subsec_pat.search(text)
    block = f"{MARKER_BEGIN}\n{table_md}\n{MARKER_END}\n"
    if m:
        start = m.end()
        next_sec = re.search(r"^##\s+", text[start:], flags=re.MULTILINE)
        end = start + next_sec.start() if next_sec else len(text)
        before, after = text[:start], text[end:]
        return before + "\n" + block + ("\n" if not after.startswith("\n") else "") + after
    else:
        sep = "" if text.endswith("\n") else "\n"
        return f"{text}{sep}\n\n## Submodules\n\n{block}\n"

def main():
    root = repo_root_from_cwd()  # <- superproject root
    readme = root / "README.md"
    table_md = build_table(root)
    if not readme.exists():
        readme.write_text(f"## Submodules\n\n{MARKER_BEGIN}\n{table_md}\n{MARKER_END}\n", encoding="utf-8")
        print("✅ README created with submodule table (fast, no network).")
        return
    text = readme.read_text(encoding="utf-8", errors="ignore")
    updated = replace_with_markers(text, table_md)
    if updated is None:
        updated = replace_existing_table(text, table_md)
    if updated is None:
        updated = ensure_submodules_section(text, table_md)
    readme.write_text(updated, encoding="utf-8")
    print("✅ Submodule table updated (fast, no network).")

if __name__ == "__main__":
    main()
