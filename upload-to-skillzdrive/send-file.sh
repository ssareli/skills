#!/bin/bash
# send-file.sh — Upload a local .zip or .skill file to SkillzDrive.
#
# Unlike the legacy version, this script does NOT embed an API key. Instead
# the caller mints a short-lived single-use upload token via the
# `skills_createUploadTicket` MCP tool and passes it in via --upload-token.
#
# Usage:
#   bash send-file.sh --file <path> --upload-token <ut_live_...> [--server-url <url>]

SERVER_URL="https://www.skillzdrive.com"
FILE_PATH=""
UPLOAD_TOKEN=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --file)
      FILE_PATH="$2"
      shift 2
      ;;
    --upload-token)
      UPLOAD_TOKEN="$2"
      shift 2
      ;;
    --server-url)
      SERVER_URL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: bash send-file.sh --file <path> --upload-token <token> [--server-url <url>]" >&2
      exit 1
      ;;
  esac
done

if [ -z "$FILE_PATH" ]; then
  echo '{"error": "Missing --file. Usage: bash send-file.sh --file <path> --upload-token <token>"}' >&2
  exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
  echo "{\"error\": \"File not found: $FILE_PATH\"}" >&2
  exit 1
fi

if [ -z "$UPLOAD_TOKEN" ]; then
  echo '{"error": "Missing --upload-token. Call skills_createUploadTicket via MCP to mint one."}' >&2
  exit 1
fi

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $UPLOAD_TOKEN" \
  -F "file=@$FILE_PATH" \
  "${SERVER_URL}/api/uploads/process-skill")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -ne 200 ] && [ "$HTTP_CODE" -ne 201 ]; then
  echo "{\"error\": \"Upload failed with status $HTTP_CODE\", \"details\": $BODY}" >&2
  exit 1
fi

echo "$BODY"
