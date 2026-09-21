#!/usr/bin/env bash

set -Eeuo pipefail

AIRBYTE_URL="${AIRBYTE_URL:-http://192.168.100.20:8000}"
AIRBYTE_CONNECTION_ID="${AIRBYTE_CONNECTION_ID:-b468d1dd-2af8-47f6-9778-0bd16fe1514a}"
AIRBYTE_CONTROL_PLANE="${AIRBYTE_CONTROL_PLANE:-airbyte-abctl-control-plane}"
AIRBYTE_NAMESPACE="${AIRBYTE_NAMESPACE:-airbyte-abctl}"
AIRBYTE_AUTH_SECRET="${AIRBYTE_AUTH_SECRET:-airbyte-auth-secrets}"
DBT_CONTAINER="${DBT_CONTAINER:-dbt}"
DBT_PROFILES_DIR="${DBT_PROFILES_DIR:-/root/.dbt}"
POLL_SECONDS="${POLL_SECONDS:-5}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-1800}"

log() {
    printf '[refresh] %s\n' "$*"
}

fail() {
    printf '[refresh] ERROR: %s\n' "$*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

secret_value() {
    local key="$1"
    docker exec "$AIRBYTE_CONTROL_PLANE" kubectl \
        -n "$AIRBYTE_NAMESPACE" \
        get secret "$AIRBYTE_AUTH_SECRET" \
        -o "jsonpath={.data.${key}}" \
        | base64 -d
}

airbyte_token() {
    local client_id client_secret response
    client_id="$(secret_value instance-admin-client-id)"
    client_secret="$(secret_value instance-admin-client-secret)"

    response="$(curl -fsS -X POST \
        "${AIRBYTE_URL}/api/public/v1/applications/token" \
        -H 'Content-Type: application/json' \
        --data "{\"client_id\":\"${client_id}\",\"client_secret\":\"${client_secret}\",\"grant_type\":\"client_credentials\"}")"

    printf '%s' "$response" \
        | python3 -c 'import json, sys; print(json.load(sys.stdin)["access_token"])'
}

require_command curl
require_command docker
require_command python3

log "Requesting Airbyte API token"
token="$(airbyte_token)"
auth_header="Authorization: Bearer ${token}"

log "Starting Airbyte sync for connection ${AIRBYTE_CONNECTION_ID}"
sync_response="$(curl -fsS -X POST \
    "${AIRBYTE_URL}/api/v1/connections/sync" \
    -H "$auth_header" \
    -H 'Content-Type: application/json' \
    --data "{\"connectionId\":\"${AIRBYTE_CONNECTION_ID}\"}")"
job_id="$(printf '%s' "$sync_response" \
    | python3 -c 'import json, sys; print(json.load(sys.stdin)["job"]["id"])')"

log "Airbyte job started: ${job_id}"
start_time="$(date +%s)"

while true; do
    job_response="$(curl -fsS \
        -X POST "${AIRBYTE_URL}/api/v1/jobs/get_without_logs" \
        -H "$auth_header" \
        -H 'Content-Type: application/json' \
        --data "{\"id\":${job_id}}")"
    job_status="$(printf '%s' "$job_response" \
        | python3 -c 'import json, sys; print(json.load(sys.stdin)["job"]["status"])')"

    case "$job_status" in
        succeeded)
            log "Airbyte sync succeeded"
            break
            ;;
        failed|cancelled|incomplete)
            printf '%s\n' "$job_response" >&2
            fail "Airbyte sync ended with status: ${job_status}"
            ;;
        *)
            elapsed=$(( $(date +%s) - start_time ))
            if (( elapsed >= TIMEOUT_SECONDS )); then
                fail "Timed out waiting for Airbyte job ${job_id}"
            fi
            log "Airbyte status: ${job_status}; waiting ${POLL_SECONDS}s"
            sleep "$POLL_SECONDS"
            ;;
    esac
done

log "Building dbt models and running tests"
docker exec "$DBT_CONTAINER" dbt build --profiles-dir "$DBT_PROFILES_DIR"

log "Analytics refresh completed successfully"
