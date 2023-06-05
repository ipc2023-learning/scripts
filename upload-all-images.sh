#! /bin/bash

set -euo pipefail

# Change into current directory.
cd "$(dirname "$0")"

cd ../

rsync -avh --progress images/ nsc:/proj/dfsplan/users/x_jense/ipc2023-learning/images/
