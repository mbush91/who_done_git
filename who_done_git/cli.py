import argparse
import os
import subprocess
import logging
from collections import Counter, defaultdict
from typing import Dict, List


def get_git_root(path: str) -> str:
    """Find the git root directory for a given path."""
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RuntimeError(f"Directory {path} is not inside a git repository.")


def get_files_in_directory(directory: str) -> List[str]:
    """Recursively get all files in the directory (excluding .git and pycache)."""
    files = []
    for root, dirs, filenames in os.walk(directory):
        if ".git" in dirs:
            dirs.remove(".git")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        for filename in filenames:
            if filename.endswith(".pyc"):
                continue
            files.append(os.path.join(root, filename))
    return files


def get_git_committers(files: List[str], repo_dir: str) -> Dict[str, Counter]:
    """Return a mapping from file to Counter of committers."""
    committers = defaultdict(Counter)
    for file in files:
        rel_file = os.path.relpath(file, repo_dir)
        try:
            result = subprocess.run(
                ["git", "-C", repo_dir, "log", "--pretty=format:%an", "--", rel_file],
                capture_output=True,
                text=True,
                check=True,
            )
            authors = result.stdout.strip().split("\n") if result.stdout else []
            committers[rel_file].update(authors)
        except subprocess.CalledProcessError:
            continue  # skip files not tracked by git
    return committers


def print_summary(committers: Dict[str, Counter]):
    print("Git Committer Summary by User:\n")
    # user -> list of (file, percent, count)
    user_files = {}
    for file, counter in committers.items():
        total_lines = sum(counter.values())
        for committer, count in counter.items():
            percent = (count / total_lines) * 100 if total_lines else 0
            user_files.setdefault(committer, []).append((file, percent, count))
    # Sort users by total lines descending
    users_sorted = sorted(
        user_files.items(), key=lambda item: -sum(f[2] for f in item[1])
    )
    for user, files in users_sorted:
        print(f"{user}:")
        for file, percent, count in sorted(files):
            print(f"  {file}: {percent:.1f}% ({count} lines)")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Summarize git committers for files in a directory."
    )
    parser.add_argument("directory", help="Target subdirectory to analyze")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show debug output"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="[%(levelname)s] %(message)s",
    )
    logger = logging.getLogger("who-done-git")

    target_dir = os.path.abspath(args.directory)
    try:
        git_root = get_git_root(target_dir)
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    files = get_files_in_directory(target_dir)
    logger.debug(f"Files found in {target_dir}:")
    for f in files:
        logger.debug(f"  {f}")

    # Get list of tracked files (relative to git root)
    try:
        tracked = subprocess.run(
            ["git", "-C", git_root, "ls-files", target_dir],
            capture_output=True,
            text=True,
            check=True,
        )
        tracked_files = set(
            os.path.normpath(os.path.join(git_root, f))
            for f in tracked.stdout.strip().split("\n")
            if f
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running git ls-files: {e}")
        return

    committers = defaultdict(Counter)
    for file in files:
        if os.path.normpath(file) not in tracked_files:
            logger.debug(f"Skipping untracked file: {file}")
            continue
        rel_file = os.path.relpath(file, git_root)
        logger.debug(f"Running git blame for: {rel_file}")
        try:
            result = subprocess.run(
                ["git", "-C", git_root, "blame", "--line-porcelain", rel_file],
                capture_output=True,
                text=True,
                check=True,
            )
            authors = []
            for line in result.stdout.splitlines():
                if line.startswith("author "):
                    author = line[len("author ") :]
                    authors.append(author)
            logger.debug(f"git blame authors for {rel_file}: {authors}")
            committers[rel_file].update(authors)
        except subprocess.CalledProcessError as e:
            logger.debug(f"git blame failed for {rel_file}: {e}")
            continue  # skip files not tracked by git
    print_summary(committers)


if __name__ == "__main__":
    main()
