# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 The Linux Foundation

"""Test that ``packer init`` failures surface where they happen.

The plugin initialisation step used to run ``packer init ... || true``
when ``packer_template`` was set, so an init failure passed silently and
resurfaced later as a bare ``Error: Missing plugins``. validate-packer.sh
caught its own init failure, but discarded Packer's explanation.

The fixture requires a plugin from a non-GitHub source. Packer rejects
that before any network access, so init fails the same way on every run,
offline and regardless of API rate limits.
"""

import os
import subprocess
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
INIT_STEP = "Initialize Packer plugins"
UNRESOLVABLE_SOURCE = "example.invalid/lfreleng/unresolvable"

UNRESOLVABLE_TEMPLATE = f"""
packer {{
  required_plugins {{
    unresolvable = {{
      source  = "{UNRESOLVABLE_SOURCE}"
      version = ">= 1.0.0"
    }}
  }}
}}

source "null" "builder" {{
  communicator = "none"
}}

build {{
  sources = ["source.null.builder"]
}}
"""

PLUGINLESS_TEMPLATE = """
source "null" "builder" {
  communicator = "none"
}

build {
  sources = ["source.null.builder"]
}
"""


def _init_step_script() -> str:
    """Return the init step's script, read from the action metadata."""
    action = yaml.safe_load((REPO_ROOT / "action.yaml").read_text(encoding="utf-8"))
    for step in action["runs"]["steps"]:
        if step.get("name") == INIT_STEP:
            return step["run"]
    raise AssertionError(f"step not found in action.yaml: {INIT_STEP}")


def _run(command: list[str], cwd: Path, **env: str) -> subprocess.CompletedProcess[str]:
    """Run a command with an empty, private Packer plugin directory."""
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PACKER_PLUGIN_PATH": str(cwd / "plugins"), **env},
    )


def test_init_step_fails_on_unresolvable_plugin(tmp_path: Path) -> None:
    """With packer_template set, a failed init fails the init step."""
    (tmp_path / "builder.pkr.hcl").write_text(UNRESOLVABLE_TEMPLATE)

    result = _run(
        ["bash", "-c", _init_step_script()],
        tmp_path,
        PACKER_TEMPLATE="builder.pkr.hcl",
    )

    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    # Packer's own explanation must be in this step's log.
    assert UNRESOLVABLE_SOURCE in output, output


def test_init_step_succeeds_when_plugins_resolve(tmp_path: Path) -> None:
    """With packer_template set, a successful init passes the step."""
    (tmp_path / "builder.pkr.hcl").write_text(PLUGINLESS_TEMPLATE)

    result = _run(
        ["bash", "-c", _init_step_script()],
        tmp_path,
        PACKER_TEMPLATE="builder.pkr.hcl",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_validate_script_shows_init_error(tmp_path: Path) -> None:
    """validate-packer.sh prints Packer's error when init fails."""
    template_dir = tmp_path / "packer"
    template_dir.mkdir()
    (template_dir / "builder.pkr.hcl").write_text(UNRESOLVABLE_TEMPLATE)

    result = _run([str(REPO_ROOT / "scripts" / "validate-packer.sh")], tmp_path)

    assert result.returncode == 1, result.stdout
    assert "Init failed" in result.stdout, result.stdout
    assert UNRESOLVABLE_SOURCE in result.stdout, result.stdout
