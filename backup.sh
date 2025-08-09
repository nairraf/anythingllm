#!/bin/bash

echo "Stopping AnythingLLM"
docker stop anythingllm

echo "Backing Up AnythingLLM Storage"
cd /data01/
tar -zcf /azstorage/backups/anythingllm-backup-$(date +%F).tar.gz anythingllm-storage

echo "Starting AnythingLLM"
docker start anythingllm
