#!/bin/bash

set -euo pipefail

IMAGE=${1}
TIME_LIMIT=${2}
MEMORY_LIMIT=${3}
shift 3  # Forget first three arguments.
ARGS=("$@")  # Collect all remaining arguments.

runsolver -C ${TIME_LIMIT} -V ${MEMORY_LIMIT} -w watch.log -v values.log apptainer run -C -H ${PWD} ${IMAGE} "${ARGS[@]}"
