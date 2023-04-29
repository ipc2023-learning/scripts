#! /bin/bash

set -euo pipefail

cd $(dirname "$0")

OUTDIR=.
mkdir -p ${OUTDIR}

for recipe in Apptainer.* ; do
    name="${recipe##*.}"
    apptainer build ${OUTDIR}/${name}.sif ${recipe}
done

echo "Finished building images"
