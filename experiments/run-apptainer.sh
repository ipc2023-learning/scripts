#!/bin/bash

set -euo pipefail

IMAGE=${1}
TIME_LIMIT=${2}
MEMORY_LIMIT=${3}
shift 3  # Forget first three arguments.
ARGS=("$@")  # Collect all remaining arguments.

# Disable swapping by setting swap limit equal to memory limit.
runsolver --wall-clock-limit ${TIME_LIMIT} --delay 60 -w watch.log -v values.log apptainer run --memory ${MEMORY_LIMIT}M --memory-swap ${MEMORY_LIMIT}M -C -H ${PWD} ${IMAGE} "${ARGS[@]}"
