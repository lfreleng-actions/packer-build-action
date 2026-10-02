#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

#############################################################################
# Packer Template Validation Script
#
# Validates Packer templates with syntax-only checking (no credentials needed)
#############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

echo "======================================"
echo "Packer Template Validation"
echo "======================================"

# Find all Packer templates
if [[ -d "packer" ]]; then
    PACKER_DIR="packer"
elif [[ -d "common-packer" ]]; then
    PACKER_DIR="common-packer"
else
    PACKER_DIR="."
fi

echo "Searching for Packer templates in: $PACKER_DIR"

# Find all .pkr.hcl files. Read null-delimited results into an array:
# a newline-separated string iterated as `for t in $TEMPLATES` splits on
# IFS and glob-expands, so any path containing whitespace breaks apart
# into several non-existent paths. shellcheck does not flag that form,
# because splitting in a `for` is usually deliberate.
#
# The trailing slash on the search directory matters. common-packer is
# conventionally a symlink, and find does not descend a symlinked
# starting point, so without it discovery silently returns nothing and
# validation reports success having checked no templates at all.
TEMPLATES=()
while IFS= read -r -d '' template; do
    TEMPLATES+=("$template")
done < <(find "$PACKER_DIR/" -name "*.pkr.hcl" -type f -print0 2>/dev/null)

if [[ ${#TEMPLATES[@]} -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  No Packer templates found${NC}"
    exit 0
fi

echo "Found templates:"
printf '%s\n' "${TEMPLATES[@]}"
echo ""

# Validate each template
for template in "${TEMPLATES[@]}"; do
    echo "Validating: $template"

    # Initialize Packer. Keep the output so a failure can show why;
    # running init again to reproduce it would repeat the plugin
    # lookups that may have failed on a rate limit in the first place.
    echo "  Initializing..."
    if init_output=$(packer init "$template" 2>&1); then
        echo -e "  ${GREEN}✓${NC} Init successful"
    else
        echo -e "  ${RED}✗${NC} Init failed"
        printf '%s\n' "$init_output"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Validate syntax only (no vars needed)
    echo "  Checking syntax..."
    if packer validate -syntax-only "$template" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Syntax valid"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗${NC} Syntax invalid"
        packer validate -syntax-only "$template" || true
        FAILED=$((FAILED + 1))
    fi

    echo ""
done

# Summary
echo "======================================"
echo "Validation Summary"
echo "======================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}Failed: $FAILED${NC}"
else
    echo -e "Failed: $FAILED"
fi
echo "======================================"

if [[ $FAILED -gt 0 ]]; then
    exit 1
fi

echo -e "${GREEN}✅ All $PASSED validations passed${NC}"
exit 0
