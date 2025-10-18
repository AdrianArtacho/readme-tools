#!/usr/bin/env python3
"""
update_table.py

Generate a Markdown table summarizing submodules from the .gitmodules file
located ONE LEVEL ABOVE this script (../.gitmodules). By default, only
root-level submodules (paths without a slash) are included. Use --subdir to
restrict to submodules whose path begins with a given folder (e.g. ".Ressources"
or "resources").

For each submodule, the script attempts to extract:
- name
- path
- url
- description (from DESCRIPTION, README*, pyproject.toml, package.json)
- a representative image (cover/thumbnail/logo/... or any image found)

Output is printed to stdout or written to --out.
"""

import argparse
import configparser
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
IMAGE_PRIORITY_NAMES = ("cover", "thumbnail", "thumb", "logo", "banner", "preview", "image", "screenshot")

# ------------------------------ CLI ------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Create a Markdown table of submodules with descriptions and images."
    )
    p.add_argument(
        "--subdir",
        metavar="FOLDER",
        default=None,
        help=(
            "Only include submodules whose *path* starts with this folder "
            "(e.g. '.Ressources' or 'resources'). If omitted, only root-level "
            "submodules are included."
        ),
    )
    p.add_argument(
        "--gitmodules",
        default=None,
        help="Optional explicit path to a .gitmodules file. Default: ../.gitmodules relative to this script.",
    )
    p.add_argument(
        "--repo-root",
        default=None,
        help="Optional explicit path to the repository root (the directory that contains .gitmodules). "
             "Default: the parent of this script (..). Used for resolving submodule paths and image links.",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Write the Markdown table to this file instead of stdout.",
    )
    p.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="How deep to search within each submodule for a representative image (default: 2).",
    )
    p.add_argument(
        "--no-images",
        action="store_true",
        help="Skip image discovery and omit the Image column.",
    )
    return p.parse_args()


# --------------------------- Utilities ---------------------------

def read_gitmodules(gitmodules_path: Path) -> List[Dict[str, str]]:
    """
    Parse .gitmodules and return a list of dicts with keys: name, path, url.
    """
    if not gitmodules_path.exists():
        raise FileNotFoundError(f".gitmodules not found at: {gitmodules_path}")

    # .gitmodules is INI-like but with sections like: submodule "name"
    # We'll parse it with configparser by normalizing section headers.
    text = gitmodules_path.read_text(encoding="utf-8", errors="ignore")

    # Convert [submodule "X"] into [submodule:X] so configparser can handle it.
    text_norm = re.sub(r'^\s*\[submodule\s+"([^"]+)"\]\s*$', r'[submodule:\1]', text, flags=re.MULTILINE)

    cfg = configparser.ConfigParser()
    cfg.read_string(text_norm)

    submodules: List[Dict[str, str]] = []
    for section in cfg.sections():
        if not section.startswith("submodule:"):
            continue
        name = section.split("submodule:", 1)[1]
        path = cfg.get(section, "path", fallback="").strip()
        url  = cfg.get(section, "url", fallback="").strip()
        if path:
            submodules.append({"name": name, "path": path, "url": url})
    return submodules


def is_in_subdir(mod_path: str, subdir: Optional[str]) -> bool:
    """
    If subdir is None => only root-level submodules (path has exactly one segment).
    If subdir is provided => include only those whose path begins with that folder.
    """
    mod_parts = Path(mod_path.strip("/")).parts
    if subdir is None:
        return len(mod_parts) == 1
    sub_parts = Path(subdir.strip("/")).parts
    return mod_parts[:len(sub_parts)] == sub_parts


def find_description(mod_dir: Path) -> Optional[str]:
    """
    Try to extract a human-friendly description from files inside the submodule.
    Priority:
      1) DESCRIPTION (plain text, first non-empty line)
      2) README.md / README.* (first non-empty line that is not a heading marker only)
      3) pyproject.toml [project] description
      4) package.json "description"
    """
    # 1) DESCRIPTION
    desc_file = mod_dir / "DESCRIPTION"
    if desc_file.exists():
        for line in desc_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if s:
                return s

    # 2) README.*
    for readme in sorted(mod_dir.glob("README*")):
        if readme.is_file():
            lines = readme.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines:
                s = line.strip().lstrip("#").strip()
                if s:
                    return s

    # 3) pyproject.toml
    pyproj = mod_dir / "pyproject.toml"
    if pyproj.exists():
        try:
            # very lightweight parse to find 'description = "..."
            txt = pyproj.read_text(encoding="utf-8", errors="ignore")
            # Look for description in [project] section
            m = re.search(r'(?ms)^\s*\[project\].*?^\s*description\s*=\s*"(.*?)"\s*$', txt)
            if m:
                return m.group(1).strip()
        except Exception:
            pass

    # 4) package.json
    pkg = mod_dir / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
            desc = data.get("description")
            if isinstance(desc, str) and desc.strip():
                return desc.strip()
        except Exception:
            pass

    return None


def find_image(mod_dir: Path, max_depth: int = 2) -> Optional[Path]:
    """
    Locate a representative image file within mod_dir up to max_depth levels deep.
    Prefer names in IMAGE_PRIORITY_NAMES.
    """
    if max_depth < 0:
        return None

    candidates: List[Path] = []
    # BFS limited depth search
    queue: List[Tuple[Path, int]] = [(mod_dir, 0)]
    while queue:
        current, depth = queue.pop(0)
        if depth > max_depth:
            continue

        try:
            for entry in current.iterdir():
                name_lower = entry.name.lower()
                if entry.is_dir():
                    # skip VCS/admin dirs
                    if name_lower in {".git", ".github", ".gitlab"}:
                        continue
                    queue.append((entry, depth + 1))
                else:
                    if entry.suffix.lower() in IMAGE_EXTS:
                        candidates.append(entry)
        except PermissionError:
            continue

    if not candidates:
        return None

    # Prioritize by filename keywords
    def score(p: Path) -> Tuple[int, int]:
        stem = p.stem.lower()
        pri = min((i for i, key in enumerate(IMAGE_PRIORITY_NAMES) if key in stem), default=999)
        # prefer shallower paths (fewer parts)
        depth = len(p.relative_to(mod_dir).parts)
        return (pri, depth)

    candidates.sort(key=score)
    return candidates[0]


def make_markdown_table(rows: List[Dict[str, str]], include_images: bool) -> str:
    headers = ["Name", "Path", "URL", "Description"]
    if include_images:
        headers.append("Image")

    md = []
    md.append("| " + " | ".join(headers) + " |")
    md.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for r in rows:
        row_vals = [
            r.get("name", ""),
            f"`{r.get('path','')}`",
            f"[link]({r.get('url','')})" if r.get("url") else "",
            r.get("description", ""),
        ]
        if include_images:
            img = r.get("image", "")
            if img:
                # Render as markdown image; width control is up to renderer. Keep relative path.
                row_vals.append(f"![image]({img})")
            else:
                row_vals.append("")
        md.append("| " + " | ".join(row_vals) + " |")

    return "\n".join(md)


def main() -> int:
    args = parse_args()

    this_dir = Path(__file__).resolve().parent
    repo_root = Path(args.repo_root) if args.repo_root else this_dir.parent
    gitmodules_path = Path(args.gitmodules) if args.gitmodules else (repo_root / ".gitmodules")

    try:
        submodules = read_gitmodules(gitmodules_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    # Filter per --subdir / root-level
    selected = [m for m in submodules if is_in_subdir(m["path"], args.subdir)]

    # Build rows
    rows: List[Dict[str, str]] = []
    for m in sorted(selected, key=lambda x: x["name"].lower()):
        path_rel = Path(m["path"])
        mod_dir = (repo_root / path_rel).resolve()

        desc = find_description(mod_dir) or ""
        img_rel_str = ""
        if not args.no_images:
            img_path = find_image(mod_dir, max_depth=args.max_depth)
            if img_path:
                try:
                    # Make image path relative to repo_root for stable links in Markdown
                    img_rel = img_path.resolve().relative_to(repo_root.resolve())
                    img_rel_str = str(img_rel).replace("\\", "/")
                except Exception:
                    img_rel_str = str(img_path)

        rows.append({
            "name": m.get("name", ""),
            "path": str(path_rel).replace("\\", "/"),
            "url": m.get("url", ""),
            "description": desc,
            "image": img_rel_str,
        })

    table = make_markdown_table(rows, include_images=not args.no_images)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(table, encoding="utf-8")
        print(f"Wrote Markdown table to: {out_path}")
    else:
        print(table)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
