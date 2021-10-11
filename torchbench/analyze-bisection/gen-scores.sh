WORKDIR=$PWD
pushd $HOME/git/benchmark
python compute_score.py --score_version v1 --benchmark_data_dir $1
popd
