#!/bin/sh

set -euo pipefail

# Must run on the v0 branch of pytorch/benchmark

TORCHBENCH_ROOT=${HOME}/xz-use/benchmark

DATA_DIR=${HOME}/xz-use/abtest
BENCHMARK_FILTER="(Background_Matting)"

pushd $TORCHBENCH_ROOT
bash .github/scripts/run-v0.sh $DATA_DIR $BENCHMARK_FILTER
