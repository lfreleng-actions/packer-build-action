# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Test script discovery functionality."""

import os
import subprocess
import tempfile
from pathlib import Path


def test_discover_templates_finds_pkr_files():
    """Test that discover-templates.sh finds .pkr.hcl files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test template
        template_dir = Path(tmpdir) / "packer"
        template_dir.mkdir()
        (template_dir / "test.pkr.hcl").write_text("# test template")

        # Run discovery script
        script_path = Path(__file__).parent.parent / "scripts" / "discover-templates.sh"
        result = subprocess.run(
            [str(script_path)],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env={**os.environ, "GITHUB_OUTPUT": str(Path(tmpdir) / "output.txt")},
        )

        assert result.returncode == 0
        assert "packer/test.pkr.hcl" in result.stdout


def test_discover_templates_no_templates():
    """Test discovery script with no templates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(__file__).parent.parent / "scripts" / "discover-templates.sh"
        result = subprocess.run(
            [str(script_path)],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env={**os.environ, "GITHUB_OUTPUT": str(Path(tmpdir) / "output.txt")},
        )

        assert result.returncode == 1
        assert "No Packer templates found" in result.stdout


def test_discover_templates_finds_var_files():
    """Test that discover-templates.sh finds .pkrvars.hcl files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test template and vars
        template_dir = Path(tmpdir) / "packer"
        template_dir.mkdir()
        (template_dir / "test.pkr.hcl").write_text("# test template")

        vars_dir = Path(tmpdir) / "vars"
        vars_dir.mkdir()
        (vars_dir / "test.pkrvars.hcl").write_text("# test vars")

        # Run discovery script
        script_path = Path(__file__).parent.parent / "scripts" / "discover-templates.sh"
        result = subprocess.run(
            [str(script_path)],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env={**os.environ, "GITHUB_OUTPUT": str(Path(tmpdir) / "output.txt")},
        )

        assert result.returncode == 0
        assert "packer/test.pkr.hcl" in result.stdout
        assert "vars/test.pkrvars.hcl" in result.stdout
