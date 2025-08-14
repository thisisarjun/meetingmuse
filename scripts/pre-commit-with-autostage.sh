#!/bin/bash
set -e

echo "Running pre-commit hooks..."

# Run pre-commit and capture the exit code
if pre-commit run --all-files; then
    echo "✅ All pre-commit hooks passed!"
    exit 0
else
    EXIT_CODE=$?

    # Check if there are any unstaged changes (indicating formatters made changes)
    if ! git diff --quiet; then
        echo "📝 Pre-commit hooks made formatting changes. Auto-staging them..."

        # Stage all modified files
        git add -u

        # Re-run pre-commit to ensure everything passes
        echo "🔄 Re-running pre-commit hooks after staging changes..."
        if pre-commit run --all-files; then
            echo "✅ All pre-commit hooks passed after auto-staging!"
            exit 0
        else
            echo "❌ Pre-commit hooks still failing after auto-staging. Please review manually."
            exit 1
        fi
    else
        # No formatting changes, so this was a real failure
        echo "❌ Pre-commit hooks failed (not due to formatting changes)"
        exit $EXIT_CODE
    fi
fi
