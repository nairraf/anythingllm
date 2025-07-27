#!/bin/bash

docker stop anythingllm

docker rm anythingllm

docker pull mintplexlabs/anythingllm:latest


docker run -d --restart unless-stopped --name anythingllm \
  --memory="3g" \
  --memory-swap="4g" \
  --cpus="2" \
  --shm-size="1g" \
  --cap-add SYS_ADMIN \
  -p 3001:3001 \
  -v /data01/anythingllm-storage:/app/server/storage \
  -v /data01/anythingllm-storage/.env:/app/server/.env \
  -e STORAGE_DIR="/app/server/storage" \
  mintplexlabs/anythingllm

