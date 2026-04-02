#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash templates/bytedcli-rpc-call.sh [cluster]
# Example:
#   bash templates/bytedcli-rpc-call.sh default

CLUSTER="${1:-default}"
BODY_FILE="$(dirname "$0")/heartbeat-body.json"

bytedcli api-test rpc-call \
  --psm vai.cvcg.aigc_editor \
  --func heartbeat \
  --env ppe_duoshan_hamlet \
  --cluster "${CLUSTER}" \
  --idc lf \
  --zone cn \
  --idl-source 2 \
  --idl-version 1.0.18 \
  --online false \
  --body-file "${BODY_FILE}"
