# 1. Base builder stage with full Debian Bookworm
FROM python:3.12-bookworm AS base

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=true \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    QR_CODE_DIR=/myapp/qr_codes

WORKDIR /myapp

# Install system deps, including pinned libc-bin with --allow-downgrades
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev \
 && apt-get install -y --allow-downgrades libc-bin=2.36-9+deb12u7 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps into a venv
COPY requirements.txt .
RUN python -m venv /.venv \
 && . /.venv/bin/activate \
 && pip install --upgrade pip \
 && pip install -r requirements.txt

# 2. Final runtime image (slim)  
FROM python:3.12-slim-bookworm AS final

# Re‑apply the same libc‑bin pin
RUN apt-get update \
 && apt-get install -y --allow-downgrades libc-bin=2.36-9+deb12u7 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copy in the venv from builder
COPY --from=base /.venv /.venv

# Ensure venv’s python & pip are on PATH
ENV PATH="/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    QR_CODE_DIR=/myapp/qr_codes

WORKDIR /myapp

# Run as non‑root
RUN useradd -m myuser
USER myuser

# Copy application code
COPY --chown=myuser:myuser . .

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
