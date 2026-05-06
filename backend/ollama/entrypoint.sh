#!/bin/sh

set -eu

MODEL_NAME="${OLLAMA_MODEL:-qwen2.5-coder:3b}"

# Start ollama in the background.
ollama serve &
SERVER_PID=$!

cleanup() {
    kill "$SERVER_PID" >/dev/null 2>&1 || true
}

trap cleanup INT TERM EXIT

echo "Waiting for Ollama server to start..."
until ollama list >/dev/null 2>&1; do
    sleep 2
done

echo "Ollama server is ready"
echo "Checking for ${MODEL_NAME} model..."

if ! ollama list | grep -q "$MODEL_NAME"; then
    echo "Pulling ${MODEL_NAME} model..."
    ollama pull "$MODEL_NAME"
else
    echo "Model ${MODEL_NAME} already exists"
fi

echo "Ollama ready with ${MODEL_NAME} model"

trap - INT TERM EXIT
wait "$SERVER_PID"
