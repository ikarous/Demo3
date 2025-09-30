# ---- Base Image ----
# Use Python 3.12 on Alpine Linux for a minimal image size
FROM python:3.12-alpine

# Python environment variables:
# PYTHONDONTWRITEBYTECODE=1 - Prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED=1 - Forces Python output to be sent straight to terminal (no buffering)
#                      This is important for seeing logs in Docker containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---- System Dependencies ----
# Install Alpine packages needed for building Python packages with C extensions
# These are required for packages like bcrypt and cryptography:
#   - build-base: Compiler and build tools (gcc, make, etc.)
#   - libffi-dev: Foreign Function Interface library (for cryptography)
#   - openssl-dev: OpenSSL development files (for SSL/TLS support)
#   - musl-dev: C standard library for Alpine Linux
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    musl-dev

# ---- Application Setup ----
# Set working directory inside the container
WORKDIR /app

# ---- Install Python Dependencies ----
# Copy requirements.txt first for better Docker layer caching
# If requirements.txt doesn't change, this layer is reused and pip install is skipped
COPY requirements.txt /app/requirements.txt
# Install Python packages without caching to reduce image size
RUN pip install --no-cache-dir -r /app/requirements.txt

# ---- Copy Application Files ----
# Copy application code last so code changes don't invalidate dependency layers
# Files copied:
COPY main.py /app/main.py
COPY preload_memcache.py /app/preload_memcache.py
COPY entrypoint.sh /entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /entrypoint.sh

# ---- Environment Variables ----
# Default Memcached address (uses Docker Compose service name for DNS resolution)
# Can be overridden in docker-compose.yml or at runtime
ENV MEMCACHED_ADDR=memcached:11211

# ---- Expose Port ----
# Document that the container listens on port 8000 (FastAPI default)
EXPOSE 8000

# ---- Container Startup ----
# Run the entrypoint script which preloads users and starts the FastAPI server
CMD ["/entrypoint.sh"]