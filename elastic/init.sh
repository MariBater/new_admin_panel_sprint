#!/bin/bash

echo "Waiting for Elasticsearch..."
until curl -s http://localhost:9200/_cluster/health >/dev/null; do 
    echo "Elasticsearch is not ready yet..."
    sleep 3
done

echo "Elasticsearch is up."

echo "Registering snapshot repository..."
curl -X PUT "http://localhost:9200/_snapshot/my_backup" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/mnt/backups/elasticsearch",
      "compress": true
    }
  }'

echo "Repository registered."

echo "Checking if indices exist..."
INDICES=$(curl -s http://localhost:9200/_cat/indices?h=index)

if [ -z "$INDICES" ]; then
    echo "No indices found — restoring snapshot..."
    curl -X POST "http://localhost:9200/_snapshot/my_backup/snapshot_1/_restore?wait_for_completion=true" \
      -H "Content-Type: application/json" \
      -d '{"include_global_state": true}'
    echo "Restore completed."
else
    echo "Indices already exist — skipping restore."
    echo "Found indices: $INDICES"
fi