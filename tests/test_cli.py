import os
import tempfile
import subprocess
import shutil
import sys
import pathlib
import pytest

from who_done_git import cli

def test_get_git_root(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    root = cli.get_git_root(str(repo_dir))
    assert os.path.samefile(root, str(repo_dir))

def test_get_files_in_directory(tmp_path):
    d = tmp_path / "dir"
    d.mkdir()
    (d / "file1.py").write_text("print('hi')\n")
    (d / "__pycache__").mkdir()
    (d / "__pycache__" / "junk.pyc").write_bytes(b"\x00")
    files = cli.get_files_in_directory(str(d))
    assert any("file1.py" in f for f in files)
    assert not any("__pycache__" in f or f.endswith(".pyc") for f in files)

def test_print_summary(capsys):
    committers = {
        "foo.py": {"alice": 5, "bob": 5},
        "bar.py": {"alice": 4, "bob": 6},
    }
    cli.print_summary(committers)
    out = capsys.readouterr().out
    assert "alice" in out
    assert "bob" in out
    assert "foo.py" in out
    assert "bar.py" in out
    assert "%" in out

@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_end_to_end(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    f = repo / "test.py"
    f.write_text("one\ntwo\n")
    subprocess.run(["git", "add", "test.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add test", "--author", "Alice <alice@example.com>"], cwd=repo, check=True)
    f.write_text("one\ntwo\nthree\n")
    subprocess.run(["git", "add", "test.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add line", "--author", "Bob <bob@example.com>"], cwd=repo, check=True)
    # Now, run the CLI logic on this repo
    sys.argv = ["who-done-git", str(repo)]
    cli.main()
    # Just check it runs and prints summary
    # Optionally, capture output and check for Alice and Bob
