#!/usr/bin/env bash
set -euo pipefail
if ! pgrep -x ollama >/dev/null; then
  echo "==> Starting Ollama server..."
  nohup ollama serve >/tmp/ollama.log 2>&1 &
  sleep 2
fi
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama is ready at http://localhost:11434"
else
  echo "Ollama still starting - check /tmp/ollama.log"
fi
