#!/bin/bash
# send-file.sh — Upload a local .zip or .skill file to SkillzDrive.
# Uploads and processes in one step — skill is created and added to your drive.
#
# Usage: bash send-file.sh --file <path> [--server-url <url>]

# Upload-only API key (embedded per-user by SkillzDrive)
UPLOAD_API_KEY="sk_live_RYzyHhv9WMQGhALV6ssfRVZ-Uk6432fL"

# Default server URL (override with --server-url)
SERVER_URL="https://www.skillzdrive.com"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --file)
      FILE_PATH="$2"
      shift 2
      ;;
    --server-url)
      SERVER_URL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: bash send-file.sh --file <path> [--server-url <url>]" >&2
      exit 1
      ;;
  esac
done

if [ -z "$FILE_PATH" ]; then
  echo '{"error": "Missing --file argument. Usage: bash send-file.sh --file <path>"}' >&2
  exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
  echo "{\"error\": \"File not found: $FILE_PATH\"}" >&2
  exit 1
fi

# Upload and process in one step
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $UPLOAD_API_KEY" \
  -F "file=@$FILE_PATH" \
  "${SERVER_URL}/api/uploads/process-skill")

# Split response body and status code
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -ne 200 ] && [ "$HTTP_CODE" -ne 201 ]; then
  echo "{\"error\": \"Upload failed with status $HTTP_CODE\", \"details\": $BODY}" >&2
  exit 1
fi

# Output the response (contains skill info, scriptsUploaded, filesUploaded)
echo "$BODY"
