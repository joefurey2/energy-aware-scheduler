FROM golang:1.16-alpine AS build
ENV CGO_ENABLED 0

RUN apk add openssl

# Set the working directory inside the container
WORKDIR /app

# Copy the Go module files
COPY go.mod  ./

COPY . .
RUN ls

# Build the Go application
RUN go build -v -o mutating-admission-controller cmd/main.go

FROM alpine
WORKDIR /app
COPY --from=build /app/mutating-admission-controller .
COPY --from=build /app/ssl ssl
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Set the entry point for the container
ENTRYPOINT ["./mutating-admission-controller"]
