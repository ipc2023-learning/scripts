#!/bin/bash

set -euo pipefail

# Check if the correct number of arguments are provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <command-to-execute>"
    exit 1
fi

# Define the list of directories
directories=(
    "baseline01"
    "baseline02"
    "repo01"
    "repo02"
    "repo03"
    "repo05"
    "repo08"
    "repo09"
)

# Read the command to execute
command_to_execute="$1"

# Iterate through each directory in the list
for directory in "${directories[@]}"; do
    # Check if the directory exists
    if [ ! -d "$directory" ]; then
        echo "Error: Directory not found: $directory"
        continue
    fi

    # Execute the command in the directory
    echo "Executing '$command_to_execute' in $directory"
    (
        cd "$directory" || exit
        eval "$command_to_execute"
    )
    echo
done
