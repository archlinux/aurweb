"""Tests for util/lint-migrations, run against fixture revision files."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "util" / "lint-migrations"

TEMPLATE = """\
revision = {revision}
down_revision = {down_revision}


def upgrade():
    do()


def downgrade():
    {downgrade_body}
"""


def write(tmp_path, name, revision, down_revision, downgrade_body="undo()"):
    (tmp_path / f"{name}.py").write_text(
        TEMPLATE.format(
            revision=revision,
            down_revision=down_revision,
            downgrade_body=downgrade_body,
        )
    )


def lint(tmp_path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)],
        capture_output=True,
        text=True,
    )


def test_repo_chain_is_clean():
    result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True)
    assert result.returncode == 0, result.stderr


def test_linear_chain_passes(tmp_path):
    write(tmp_path, "a", '"aaa"', "None")
    write(tmp_path, "b", '"bbb"', '"aaa"')
    result = lint(tmp_path)
    assert result.returncode == 0, result.stderr


def test_fork_and_two_heads(tmp_path):
    write(tmp_path, "a", '"aaa"', "None")
    write(tmp_path, "b", '"bbb"', '"aaa"')
    write(tmp_path, "c", '"ccc"', '"aaa"')
    result = lint(tmp_path)
    assert result.returncode == 1
    assert "fork" in result.stderr
    assert "exactly one head" in result.stderr


def test_dangling_parent(tmp_path):
    write(tmp_path, "a", '"aaa"', "None")
    write(tmp_path, "b", '"bbb"', '"zzz"')
    result = lint(tmp_path)
    assert result.returncode == 1
    assert "'zzz' does not exist" in result.stderr


def test_noop_downgrade(tmp_path):
    write(tmp_path, "a", '"aaa"', "None")
    write(tmp_path, "b", '"bbb"', '"aaa"', downgrade_body="pass")
    result = lint(tmp_path)
    assert result.returncode == 1
    assert "downgrade() is missing or a no-op" in result.stderr


def test_missing_downgrade_allowlist(tmp_path):
    write(tmp_path, "a", '"f47cad5d6d03"', "None", downgrade_body="pass")
    write(tmp_path, "b", '"bbb"', '"f47cad5d6d03"')
    result = lint(tmp_path)
    assert result.returncode == 0, result.stderr


def test_merge_revision_rejected(tmp_path):
    write(tmp_path, "a", '"aaa"', "None")
    write(tmp_path, "b", '"bbb"', "None")
    write(tmp_path, "m", '"mmm"', '("aaa", "bbb")')
    result = lint(tmp_path)
    assert result.returncode == 1
    assert "merge revisions are not supported" in result.stderr


def test_duplicate_revision(tmp_path):
    write(tmp_path, "a", '"aaa"', "None")
    write(tmp_path, "b", '"aaa"', "None")
    result = lint(tmp_path)
    assert result.returncode == 1
    assert "duplicate revision" in result.stderr


def test_syntax_error_reported(tmp_path):
    write(tmp_path, "a", '"aaa"', "None")
    (tmp_path / "broken.py").write_text("def upgrade(:\n")
    result = lint(tmp_path)
    assert result.returncode == 1
    assert "broken.py" in result.stderr
