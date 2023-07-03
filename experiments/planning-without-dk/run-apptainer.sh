#!/bin/bash

set -euo pipefail

if [[ $# != 6 ]]; then
    echo "usage: $(basename "$0") image domain_file problem_file plan_file time_limit memory_limit" 1>&2
    exit 2
fi

IMAGE=$1
DOMAIN=$(readlink -f $2)
PROBLEM=$(readlink -f $3)
PLAN=$(readlink -f $4)
TIME_LIMIT=$5
MEMORY_LIMIT=$6

if [ -f $PLAN ]; then
    echo "Error: remove $PLAN" 1>&2
    exit 2
fi

echo "Start time: $(date +%Y-%m-%dT%H:%M:%S.%3N)"
runsolver --cpu-limit ${TIME_LIMIT} --rss-swap-limit ${MEMORY_LIMIT} --delay 5 -w watch.log -v values.log apptainer run --containall --home ${PWD} ${IMAGE} ${DOMAIN} ${PROBLEM} ${PLAN}
