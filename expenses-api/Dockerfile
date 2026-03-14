# Builder stage
FROM python:3.13-alpine AS builder

WORKDIR /code

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

COPY ./requirements.txt /code/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Runtime stage
FROM python:3.13-alpine

WORKDIR /code

# Install runtime dependencies
RUN apk add --no-cache curl libgcc

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . /code

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "52" ]
