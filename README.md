# who-done-git

Summarize git committers for files in a directory.

## Installation

From the root of this repo:

```bash
pip install .
# or, if using poetry:
poetry install
```

## Usage

```bash
who-done-git <directory>
```

- `<directory>`: Path to the subdirectory you want to analyze (relative or absolute).

The tool will print a summary of git committers for all files in the specified directory.

## Example

```bash
who-done-git src/
```

---

This tool requires that you run it inside a git repository.
