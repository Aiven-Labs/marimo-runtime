FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY notebook.py .

EXPOSE 8080

# Editable mode, gated behind a token password passed in via
# MARIMO_TOKEN_PASSWORD so it's never baked into the image. Shell form
# (not exec array) so the env var expands at container start.
CMD marimo edit notebook.py --host 0.0.0.0 --port 8080 --headless --token-password "$MARIMO_TOKEN_PASSWORD"
