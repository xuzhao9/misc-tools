WORKDIR=$PWD
pushd $HOME/git/benchmark
python scripts/get_torch_nightly_wheels.py create_requirements --start_date $1 --end_date $2 --packages torch torchvision torchtext --output_dir $WORKDIR/v2-sweep-20220120
