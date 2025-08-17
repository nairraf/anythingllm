#!/bin/bash

docker stop anythingllm

docker rm anythingllm

docker system prune -a
docker volume prune

docker pull mintplexlabs/anythingllm:latest


docker run -d --restart unless-stopped --name anythingllm \
  --memory="3g" \
  --memory-swap="4g" \
  --shm-size="1g" \
  --cap-add SYS_ADMIN \
  -p 3001:3001 \
  -v /etc/localtime:/etc/localtime:ro \
  -v /etc/timezone:/etc/timezone:ro \
  -v /data01/anythingllm-storage:/app/server/storage \
  -v /data01/anythingllm-storage/.env:/app/server/.env \
  -e STORAGE_DIR="/app/server/storage" \
  mintplexlabs/anythingllm

