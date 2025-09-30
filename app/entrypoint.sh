#!/bin/sh
set -e

# Seed memcache (don't crash the container if seeding fails in a demo)
python /app/preload_memcache.py || echo "⚠️  Memcached preload failed (continuing)"

# Start the API
exec uvicorn main:app --host 0.0.0.0 --port 8000