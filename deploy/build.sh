#!/usr/bin/env bash
# MIE production build wrapper — global timeout + progress logging
# 用法: bash deploy/build.sh [timeout_seconds]
# 默认全局超时 3600s（1 小时），超过即终止并提示卡在哪一步
# 日志: /tmp/mie-build-<时间戳>.log
set -euo pipefail

cd "$(dirname "$0")/.."

BUILD_TIMEOUT="${1:-3600}"
LOG_FILE="/tmp/mie-build-$(date +%Y%m%d-%H%M%S).log"

echo "=== MIE build started $(date) ===" | tee "$LOG_FILE"
echo "Global timeout: ${BUILD_TIMEOUT}s (override: bash deploy/build.sh <seconds>)" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"

# 全局超时执行构建，输出实时写入日志
timeout "$BUILD_TIMEOUT" docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build 2>&1 | tee -a "$LOG_FILE"
status=${PIPESTATUS[0]}

if [ "$status" -eq 124 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "!!! BUILD TIMED OUT after ${BUILD_TIMEOUT}s !!!" | tee -a "$LOG_FILE"
    echo "最后 30 行日志（看卡在哪一步）:" | tee -a "$LOG_FILE"
    tail -30 "$LOG_FILE" | tee -a "$LOG_FILE"
    echo "完整日志: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 124
fi

echo "" | tee -a "$LOG_FILE"
echo "=== Build finished with status $status at $(date) ===" | tee -a "$LOG_FILE"
exit "$status"