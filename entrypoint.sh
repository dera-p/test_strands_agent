#!/bin/bash
set -e

# Lambda specific setup for Playwright
# Playwright needs write access to browsers path, but Lambda filesystem is read-only except /tmp
# So we link /tmp/pw-browsers if needed or set env var correctly (handled in Dockerfile)

# Just execute the CMD passed to docker run
exec /lambda-entrypoint.sh "$@"
