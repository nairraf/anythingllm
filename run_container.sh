#!/bin/bash

docker run -d --name anythingllm \
  --cap-add SYS_ADMIN \
  -p 3001:3001 \
  -v /data01/anythingllm-storage:/app/server/storage \
  -v /data01/anythingllm-storage/.env:/app/server/.env \
  -e STORAGE_DIR="/app/server/storage" \
  mintplexlabs/anythingllm

