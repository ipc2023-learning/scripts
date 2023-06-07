#!/bin/bash

set -euo pipefail

IMAGE=${1}
TIME_LIMIT=${2}
MEMORY_LIMIT=${3}
shift 3  # Forget first three arguments.
ARGS=("$@")  # Collect all remaining arguments.

runsolver --wall-clock-limit ${TIME_LIMIT} --rss-swap-limit ${MEMORY_LIMIT} --delay 60 -w watch.log -v values.log apptainer run -C -H ${PWD} ${IMAGE} "${ARGS[@]}"
