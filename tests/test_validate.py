# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Test validation functionality."""

import subprocess
import tempfile
from pathlib import Path


def test_validate_script_no_templates():
    """Test validation script with no templates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(__file__).parent.parent / "scripts" / "validate-packer.sh"
        result = subprocess.run(
            [str(script_path)], cwd=tmpdir, capture_output=True, text=True
        )

        # Should succeed with warning when no templates found
        assert result.returncode == 0
        assert "No Packer templates found" in result.stdout


def test_validate_script_invalid_template():
    """Test validation script with invalid template."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create invalid template
        template_dir = Path(tmpdir) / "packer"
        template_dir.mkdir()
        (template_dir / "invalid.pkr.hcl").write_text("invalid HCL syntax {")

        script_path = Path(__file__).parent.parent / "scripts" / "validate-packer.sh"
        result = subprocess.run(
            [str(script_path)], cwd=tmpdir, capture_output=True, text=True
        )

        # Should fail with syntax error
        assert result.returncode == 1
        assert (
            "Init failed" in result.stdout
            or "Syntax invalid" in result.stdout
            or "Failed: 1" in result.stdout
            or "Failed:" in result.stdout
        )


def test_validate_script_valid_template():
    """Test validation script with valid minimal template."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create valid minimal template
        template_dir = Path(tmpdir) / "packer"
        template_dir.mkdir()

        valid_template = """
packer {
  required_version = ">= 1.10.0"
  required_plugins {
    null = {
      version = "~> 3.2"
      source  = "github.com/hashicorp/null"
    }
  }
}

source "null" "example" {
  communicator = "none"
}

build {
  sources = ["source.null.example"]
}
"""
        (template_dir / "valid.pkr.hcl").write_text(valid_template)

        script_path = Path(__file__).parent.parent / "scripts" / "validate-packer.sh"
        result = subprocess.run(
            [str(script_path)], cwd=tmpdir, capture_output=True, text=True
        )

        # Should succeed
        assert result.returncode == 0
        assert (
            "✓" in result.stdout
            or "validations passed" in result.stdout
            or "Passed: 1" in result.stdout
        )
