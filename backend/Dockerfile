# backend/Dockerfile
# Coursewright — Backend Container
#
# Used in two contexts:
#   Local dev:   docker-compose.yml builds this, overrides CMD with --reload
#   Production:  CI/CD builds this, pushes to ECR, EC2 runs CMD as-is
#
# Build context is ./backend (set in docker-compose.yml and backend-ci.yml).
# All COPY paths are relative to ./backend.

# ─── Base Image ──────────────────────────────────────────────────────────────
# python:3.11-slim — Debian-based minimal Python image (~130 MB).
#
# Why 3.11-slim and not:
#   python:3.11        → Full Debian image (~900 MB). Too large.
#   python:3.11-alpine → Uses musl libc instead of glibc. Several Python
#                        packages (including some in this project) have subtle
#                        compatibility issues with musl. Not worth the 80 MB saving.
#   python:3.11-slim   → Strips debug tools and man pages from Debian.
#                        Full glibc compatibility. Right balance of size + stability.
FROM python:3.11-slim

# ─── Environment Variables ───────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
#
# PYTHONDONTWRITEBYTECODE=1
#   Stops Python from writing .pyc bytecode files inside the container.
#   Keeps the container filesystem clean. No functional impact.
#
# PYTHONUNBUFFERED=1
#   Forces stdout and stderr to be unbuffered.
#   Without this, print() and logger output is held in a buffer and may not
#   appear in `docker compose logs` for seconds after the line executes.
#   With this, every log line appears immediately.
#
# PIP_NO_CACHE_DIR=1
#   Tells pip not to cache downloaded packages inside the image.
#   We only install once during build — the cache would waste ~50 MB of image space.
#
# PIP_DISABLE_PIP_VERSION_CHECK=1
#   Suppresses the "new version of pip available" warning on every build.

# ─── Non-Root User ───────────────────────────────────────────────────────────
# Create a non-root user before any file operations.
# Running as root inside a container is a security risk:
#   - If the app has a vulnerability that allows code execution,
#     the attacker gets root inside the container.
#   - Root inside certain container configurations can lead to
#     host filesystem access.
# Running as appuser limits the blast radius to what appuser can do.
#
# --disabled-password: no password authentication (not needed for a service account)
# --gecos "":          skip the GECOS info prompts (name, phone, etc.)
RUN adduser --disabled-password --gecos "" appuser

# ─── Working Directory ───────────────────────────────────────────────────────
# All subsequent COPY, RUN, CMD instructions operate relative to /app.
# This also becomes the working directory when you exec into the container:
#   docker compose exec backend bash  →  lands you in /app
WORKDIR /app

# ─── System Dependencies ─────────────────────────────────────────────────────
# requirements.txt uses psycopg2-binary, NOT psycopg2.
# psycopg2-binary is a pre-compiled wheel that bundles the PostgreSQL client
# library inside itself. It does NOT need libpq-dev or gcc to compile.
# This saves ~200 MB of build tools and ~90 seconds of compile time.
#
# curl: lightweight HTTP tool, useful for manual health checks and debugging
#       inside a running container.
#
# --no-install-recommends: skips suggested but non-essential packages (~50 MB saved)
# rm -rf /var/lib/apt/lists/*: deletes apt package indexes after install.
#   apt-get update downloads these indexes (~40 MB). We don't need them at runtime.
#   Deleting them in the SAME RUN layer prevents them from being baked into the image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ─── Python Dependencies (Layer Cache Optimization) ──────────────────────────
# COPY requirements.txt BEFORE copying application code.
#
# Why this order matters:
#   Docker caches each layer. If the inputs to a layer haven't changed,
#   Docker reuses the cached layer and skips the RUN command entirely.
#
#   requirements.txt changes rarely (only when adding a new package).
#   Application code (.py files) changes constantly during development.
#
#   With this order:
#     - Edit a .py file → only "COPY . ." re-runs (~1 second)
#     - Add a new package → requirements.txt changes → pip install re-runs (~2 min)
#
#   If you reverse the order (COPY . . first, then requirements.txt):
#     - Edit ANY .py file → pip install re-runs every single time (~2 min)
#     - This is the most common Docker performance mistake.
#
# --chown=appuser:appuser: the copied file is owned by appuser, not root.
COPY --chown=appuser:appuser requirements.txt .

# pip runs as root here (USER appuser hasn't been set yet).
# pip installs to /usr/local/lib/python3.11/site-packages/ — not to /app.
# appuser will have read access to these packages when they run the app.
RUN pip install -r requirements.txt

# ─── Application Code ────────────────────────────────────────────────────────
# Copy the rest of the backend source code into the container.
# --chown: gives appuser ownership of all files in /app.
#
# In local development, docker-compose.yml mounts ./backend:/app OVER this.
# The mount replaces the copied files with your live local files.
# This COPY still runs (during build) to ensure the image is self-contained
# when run without a volume mount (e.g., on EC2 in production).
COPY --chown=appuser:appuser . .

# ─── Switch to Non-Root User ─────────────────────────────────────────────────
# All instructions from here on (including CMD) run as appuser.
# pip install above ran as root intentionally — it needed to write to /usr/local.
USER appuser

# ─── Port ────────────────────────────────────────────────────────────────────
# Documents that this container listens on port 8000.
# This does NOT publish the port to your host machine.
# Port publishing is handled by docker-compose.yml: "8000:8000"
# and by `docker run -p 8000:8000` in the EC2 deploy script.
EXPOSE 8000

# ─── Production Startup Command ──────────────────────────────────────────────
# This CMD runs in production (EC2 via docker run).
# docker-compose.yml overrides it with --reload for local development.
#
# --host 0.0.0.0   Required inside Docker. If you use 127.0.0.1, uvicorn
#                  only listens on the container's loopback interface and
#                  is completely unreachable from outside the container.
#                  0.0.0.0 means "listen on all network interfaces."
# --port 8000      Must match EXPOSE above and the port mapping in docker-compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]