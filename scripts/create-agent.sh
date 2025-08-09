#!/bin/bash
# Script to create new agent from template

set -e

AGENT_NAME="$1"
AGENT_TYPE="${2:-generic}"

if [ -z "$AGENT_NAME" ]; then
    echo "Usage: $0 <agent-name> [agent-type]"
    echo "Example: $0 gradle-checker-service-x inspection"
    exit 1
fi

AGENT_DIR="demo/agent-$AGENT_NAME"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create agent directory
mkdir -p "$AGENT_DIR"

# Create agent.md from template
sed "s/{AGENT_NAME}/$AGENT_NAME/g" config/agent-template.md > "$AGENT_DIR/agent.md"

# Create initial state.json
sed -e "s/{AGENT_ID}/agent-$AGENT_NAME/g" \
    -e "s/{AGENT_TYPE}/$AGENT_TYPE/g" \
    -e "s/{ISO_TIMESTAMP}/$TIMESTAMP/g" \
    config/state-template.json > "$AGENT_DIR/state.json"

# Create initial command file
echo "# Initial command for $AGENT_NAME" > "$AGENT_DIR/1.txt"
echo "# Agent created at $TIMESTAMP" >> "$AGENT_DIR/1.txt"

echo "✅ Agent '$AGENT_NAME' created successfully!"
echo "📁 Location: $AGENT_DIR"
echo "📝 Edit agent.md to define function and rules"
echo "🔧 Edit 1.txt to add first command"
echo ""
echo "Files created:"
ls -la "$AGENT_DIR/"