#!/bin/bash
# Wait for Ollama to be ready, then pull the model if not already present.
set -e

OLLAMA_HOST="${OLLAMA_BASE_URL:-http://ollama:11434}"
MODEL="${LLM_MODEL:-gemma4:e2b}"

echo "Waiting for Ollama at $OLLAMA_HOST ..."
until curl -sf "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; do
    sleep 2
done
echo "Ollama is up."

if ! curl -sf "$OLLAMA_HOST/api/tags" | grep -q "\"$MODEL\""; then
    echo "Pulling model $MODEL (this may take a few minutes on first run) ..."
    curl -sf "$OLLAMA_HOST/api/pull" -d "{\"name\": \"$MODEL\"}"
    echo "Model $MODEL ready."
else
    echo "Model $MODEL already available."
fi

exec "$@"
