# readme-tools

A lightweight, dependency-free utility to automatically generate and update a **Submodules Table** inside your meta-repository’s `README.md`.

This tool scans all submodules listed in your `.gitmodules` file and rebuilds a three-column table:

| Name | Description | Preview |
| --- | --- | :---: |

It pulls a short description from each submodule’s local `README.md` and (if available) a small GUI image from `img/gui.png`.

---

## Features

- 🧠 **Auto-detects the superproject root**  
  Works both when run from the meta-repo or from within the `readme-tools` submodule itself.

- ⚡ **Fast and offline**  
  No network calls — unreachable repos or missing images are silently skipped.

- 🖼️ **Live previews**  
  GitHub/GitLab submodules automatically show images from their latest `HEAD` commit.

- 🧹 **Self-excluding**  
  The `readme-tools` submodule itself is never listed in the generated table.

---

## Installation

Clone or add the submodule to your meta-repo:

```bash
git submodule add -b main https://github.com/yourname/readme-tools tools/readme-tools
git submodule update --init --recursive
```

---

## create a virtual environment inside the submodule

```bash
cd tools/readme-tools

# create venv (MacOS)
python3 -m venv .venv 

# activate it (MacOS)
source .venv/bin/activate
````
