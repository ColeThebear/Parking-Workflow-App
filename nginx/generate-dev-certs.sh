#!/usr/bin/env sh
# Generate a self-signed TLS certificate for local development.
# Run once from the repo root: sh nginx/generate-dev-certs.sh
#
# For production use Let's Encrypt via Certbot or Caddy instead.
set -e
mkdir -p nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/key.pem \
  -out    nginx/certs/cert.pem \
  -subj   "/C=US/ST=NY/L=Albany/O=SUNY Parking Dev/CN=localhost"
echo "Self-signed cert written to nginx/certs/"
