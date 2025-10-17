# readme-tools

2) Add it to any meta-repo
git submodule add -b main https://github.com/yourname/readme-tools tools/readme-tools
git submodule update --init --recursive

3) Run from the meta-repo root
python tools/readme-tools/update_table.py  # fast, zero-network table builder

---

Drop-in script (works from a submodule)

It detects the superproject root via git rev-parse --show-toplevel from the current working directory, so it updates that repo’s README.md, not the tools submodule.

No network calls; it skips unreachable repos or missing images (cell shows –).

Uses HEAD raw URLs for GitHub/GitLab so images render and stay up to date.

---

How to run

From the meta-repo root (your original way):

```bash
python readme-tools/update_table.py
```

From inside the submodule folder (your new request):

```bash
cd readmi-tools
python update_table.py
```

The function above will detect the superproject and update <meta-repo>/README.md there.
