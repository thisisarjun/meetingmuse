#!/bin/bash

# Smart commit script that auto-stages pre-commit formatting changes
# Usage: ./scripts/commit-with-precommit.sh "commit message"

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"commit message\""
    echo "       $0 --amend"
    exit 1
fi

echo "🚀 Starting smart commit with pre-commit auto-staging..."

# Store the commit message or flag
COMMIT_ARG="$1"

# Check if we have staged changes
if git diff --cached --quiet; then
    echo "❌ No staged changes found. Please stage your changes first with 'git add'"
    exit 1
fi

echo "📋 Staged files:"
git diff --cached --name-only

# Run pre-commit with auto-staging loop
echo "🔍 Running pre-commit hooks..."

MAX_ATTEMPTS=3
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "🔄 Pre-commit attempt $ATTEMPT/$MAX_ATTEMPTS..."

    if pre-commit run; then
        echo "✅ All pre-commit hooks passed!"
        break
    else
        EXIT_CODE=$?

        # Check if there are unstaged changes (formatters made changes)
        if ! git diff --quiet; then
            echo "📝 Pre-commit hooks made formatting changes."
            echo "🔧 Auto-staging the changes..."

            # Stage all changes (including new files that may have been created)
            git add -A

            echo "📋 Updated staged files:"
            git diff --cached --name-only

            ATTEMPT=$((ATTEMPT + 1))

            if [ $ATTEMPT -le $MAX_ATTEMPTS ]; then
                echo "🔄 Re-running pre-commit hooks..."
            fi
        else
            echo "❌ Pre-commit hooks failed (not due to formatting). Please fix and try again."
            exit $EXIT_CODE
        fi
    fi
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "❌ Pre-commit hooks still failing after $MAX_ATTEMPTS attempts. Please review manually."
    exit 1
fi

# Proceed with the commit
echo "💾 Committing changes..."
if [ "$COMMIT_ARG" = "--amend" ]; then
    git commit --amend
else
    git commit -m "$COMMIT_ARG"
fi

echo "🎉 Commit successful!"
