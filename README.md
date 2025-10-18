# readme-tools

A lightweight, dependency-free utility to automatically generate and update a **Submodules Table** inside your meta-repository’s `README.md`.

This tool scans all submodules listed in your `.gitmodules` file and rebuilds a dynamic Markdown table such as:

| Name | Path | URL | Description | Image |
| --- | --- | --- | --- | :---: |

It extracts a short description from each submodule’s local files (`DESCRIPTION`, `README`, `pyproject.toml`, `package.json`) and, if available, finds a representative image (`cover`, `logo`, `thumbnail`, etc.) up to two levels deep within each submodule folder.

---

## Features

- 🧠 **Auto-detects the superproject root**  
  Works both when run from the meta-repo or from within the `readme-tools` submodule itself.

- ⚡ **Fast and offline**  
  No network calls — unreachable repos or missing images are silently skipped.

- 🖼️ **Smart image discovery**  
  Automatically finds the most relevant image within each submodule (e.g. `cover.png`, `logo.svg`, `thumbnail.jpg`).

- 🧹 **Self-excluding**  
  The `readme-tools` submodule itself is never listed in the generated table.

- 🧩 **Folder filtering via `--subdir`**  
  By default, only submodules located at the root of the meta-repository are included.  
  Use `--subdir` to include submodules whose paths start with a specific folder (for example `.Ressources` or `resources`).

- 🧱 **Custom insertion point in `README.md`**  
  You can control *where* the table is placed by adding two special placeholder comments in your README:

  ```markdown
  <!-- SUBMODULES_TABLE_START -->
  (the table will be inserted or replaced here)
  <!-- SUBMODULES_TABLE_END -->
  ```

When these tags are present, the script replaces only the content between them.
If they are missing, the generated table is simply printed to the terminal or written as-is to the file specified by `--out`.

---

## Installation

Clone or add the submodule to your meta-repo:

```bash
git submodule add -b main https://github.com/yourname/readme-tools tools/readme-tools
git submodule update --init --recursive
```

---

## Virtual environment setup

```bash
cd tools/readme-tools

# create venv (MacOS / Linux)
python3 -m venv .venv 

# activate it (MacOS / Linux)
source .venv/bin/activate
```

---

## Usage

### Basic usage (root-level submodules)

Generate a Markdown table for all submodules directly in the repository root:

```bash
python update_table.py
```

### Filter by folder

Only include submodules whose path begins with `.Ressources/`:

```bash
python update_table.py --subdir .Ressources
```

or, equivalently:

```bash
python update_table.py --subdir resources
```

### Write output to a file

Instead of printing to the console, save the generated Markdown table to a file:

```bash
python update_table.py --out SUBMODULES.md
```

### Skip image scanning

To speed up generation or when images are irrelevant:

```bash
python update_table.py --no-images
```

### Specify custom paths

You can also explicitly set the `.gitmodules` or repository root path:

```bash
python update_table.py \
    --gitmodules /path/to/.gitmodules \
    --repo-root /path/to/meta-repo
```

---

## Example

### README with placeholder tags

Here’s a minimal example of a `README.md` that uses insertion markers:

```markdown
# My Meta-Repository

This project contains several submodules related to digital music and computation.

<!-- SUBMODULES_TABLE_START -->
(old table will be replaced automatically)
<!-- SUBMODULES_TABLE_END -->

For more information, see the documentation in each submodule.
```

When you run:

```bash
python update_table.py --subdir .Ressources --out ../README.md
```

the script will replace everything between those tags with the freshly generated Markdown table.

**Output example:**

| Name          | Path                        | URL                                               | Description    |                       Image                       |
| ------------- | --------------------------- | ------------------------------------------------- | -------------- | :-----------------------------------------------: |
| sample-module | `.Ressources/sample-module` | [link](https://github.com/yourname/sample-module) | Example module | ![image](.Ressources/sample-module/img/cover.png) |

---

## License

MIT © 2025 Adrián Artacho
