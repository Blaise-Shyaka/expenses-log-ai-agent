# Builder stage
FROM python:3.13-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "langgraph-cli[inmem]"

# Runtime stage
FROM python:3.13-alpine

WORKDIR /app

# Install runtime dependencies (curl for healthcheck, libgcc for jsonschema_rs)
RUN apk add --no-cache curl libgcc

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

EXPOSE 8123

CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8123"]
