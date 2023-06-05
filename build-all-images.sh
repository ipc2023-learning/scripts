#! /bin/bash

set -euo pipefail

prefix=Apptainer.
for recipe in $prefix* ; do
    dest="../images/${recipe#$prefix}".sif

    if [ -f "$dest" ]; then
        echo "Image $dest already exists"
    else
        echo "Image $dest does not exist --> building it now"
        time apptainer build ${dest} ${recipe}
    fi
done
