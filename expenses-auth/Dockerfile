# Builder
FROM golang:1.25-alpine AS builder

WORKDIR /code

RUN --mount=type=cache,target=/go/pkg/mod \
  --mount=type=bind,source=go.sum,target=go.sum \
  --mount=type=bind,source=go.mod,target=go.mod \
  go mod download

COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
  --mount=type=cache,target=/root/.cache/go-build \
  CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/expenses-auth .

# Runtime
FROM alpine

RUN apk add --no-cache ca-certificates
RUN addgroup -S nonrootgroup && adduser -S nonroot -G nonrootgroup

COPY --from=builder --chown=nonroot:nonrootgroup /out/expenses-auth /code/expenses-auth

USER nonroot

WORKDIR /code

EXPOSE 8001

CMD ["./expenses-auth"]
