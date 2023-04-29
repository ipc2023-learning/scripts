#! /bin/bash

set -euo pipefail

prefix=Apptainer.
for recipe in $prefix* ; do
    name="${recipe#$prefix}".sif

    if [ -f "$name" ]; then
        echo "Image $name already exists"
    else
        echo "Image $name does not exist --> building it now"
        apptainer build ${name} ${recipe}
    fi
done
