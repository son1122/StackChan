# Multi-stage Dockerfile for StackChan Core Go Server
FROM golang:1.23-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o stackChan main.go

# Minimal runtime image
FROM alpine:latest

WORKDIR /app

RUN apk add --no-cache ca-certificates tzdata

COPY --from=builder /app/stackChan /app/stackChan
COPY --from=builder /app/manifest /app/manifest
COPY --from=builder /app/resource /app/resource

EXPOSE 12800

CMD ["/app/stackChan"]
