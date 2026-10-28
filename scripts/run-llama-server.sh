#!/bin/sh
set -eu
MODEL_DIR="${MODEL_DIR:-$HOME/models}"
LLM="$MODEL_DIR/Qwen3VL-8B-Instruct-Q4_K_M.gguf"
MMPROJ="$MODEL_DIR/mmproj-Qwen3VL-8B-Instruct-F16.gguf"
exec /opt/homebrew/bin/llama-server \
  -m "$LLM" \
  --mmproj "$MMPROJ" \
  --host 127.0.0.1 \
  --port 8080 \
  -c 8192 \
  -ngl 99 \
  --jinja
