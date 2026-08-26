FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY notebook.py .

EXPOSE 8080

# A real marimo server, not a WASM export: one shared Python kernel, and
# whatever gets saved (Ctrl+S, or autosave) writes straight back to
# notebook.py on disk -- see this example's README for what that means
# for isolation, and for how long an edit actually survives.
#
# --token-password is the only thing standing between "anyone with the
# URL" and "arbitrary code execution in this container." marimo accepts
# an empty password just as readily as a real one, so this refuses to
# start at all rather than silently deploying unprotected --
# MARIMO_TOKEN_PASSWORD must be set as an environment variable on the
# Aiven Application (see README).
CMD ["sh", "-c", "if [ -z \"$MARIMO_TOKEN_PASSWORD\" ]; then echo 'MARIMO_TOKEN_PASSWORD is not set -- refusing to start without a password.' >&2; exit 1; fi; exec marimo edit notebook.py --host 0.0.0.0 --port 8080 --headless --token-password \"$MARIMO_TOKEN_PASSWORD\""]
