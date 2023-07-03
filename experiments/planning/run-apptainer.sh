#!/bin/bash

set -euo pipefail

if [[ $# != 7 ]]; then
    echo "usage: $(basename "$0") image dk_file domain_file problem_file plan_file time_limit memory_limit" 1>&2
    exit 2
fi

IMAGE=$1
DK=$(readlink -f $2)
DOMAIN=$(readlink -f $3)
PROBLEM=$(readlink -f $4)
PLAN=$(readlink -f $5)
TIME_LIMIT=$6
MEMORY_LIMIT=$7

if [ -f $PLAN ]; then
    echo "Error: remove $PLAN" 1>&2
    exit 2
fi

echo "Start time: $(date +%Y-%m-%dT%H:%M:%S.%3N)"
runsolver --cpu-limit ${TIME_LIMIT} --rss-swap-limit ${MEMORY_LIMIT} --delay 5 -w watch.log -v values.log apptainer run --containall --home ${PWD} ${IMAGE} ${DK} ${DOMAIN} ${PROBLEM} ${PLAN}
