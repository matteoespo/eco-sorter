#!/bin/bash

/bin/ollama serve &
echo "Waiting for Ollama to start..."
while ! ollama list > /dev/null 2>&1; do
  sleep 1
done

echo "Ollama is ready. Pulling model..."
# Pull the model with retries
until ollama pull gemma:2b; do
  echo "Pull failed, retrying in 3 seconds..."
  sleep 3
done

echo "Model pulled successfully. Keeping server alive."
# Wait for all background processes to finish
wait -n
