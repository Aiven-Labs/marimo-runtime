FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py schema.sql ./

# Aiven Applications injects DATABASE_URL (and other service creds) as
# environment variables at runtime when a service integration is attached
# -- nothing secret is baked into this image.
EXPOSE 8080

# Running in editable mode (marimo edit), gated behind a token password
# passed in via MARIMO_TOKEN_PASSWORD so it's never baked into the image.
# Shell form (not exec array) so the env var expands at container start.
CMD marimo edit app.py --host 0.0.0.0 --port 8080 --headless --token-password "$MARIMO_TOKEN_PASSWORD"
