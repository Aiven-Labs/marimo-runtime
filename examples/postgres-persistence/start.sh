#!/bin/sh
set -e

# api.py binds to 127.0.0.1:8000 (internal only -- nginx is the sole
# externally reachable process). Start it in the background, then exec
# nginx so nginx becomes PID 1 and the container still shuts down cleanly
# on SIGTERM.
python3 /app/api.py &
exec nginx -g 'daemon off;'
