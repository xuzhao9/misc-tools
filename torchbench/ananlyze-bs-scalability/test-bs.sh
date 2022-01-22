# Run the 

pushd ${HOME}/data/xz-use/benchmark
echo "Running eval, bs=1"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 1,self.eval_batch_size = 2,' torchbenchmark/models/timm_efficientnet/config.py
echo "Running eval, bs=2"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 2,self.eval_batch_size = 4,' torchbenchmark/models/timm_efficientnet/config.py
echo "Running eval, bs=4"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 4,self.eval_batch_size = 8,' torchbenchmark/models/timm_efficientnet/config.py
echo "Running eval, bs=8"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 8,self.eval_batch_size = 16,' torchbenchmark/models/timm_efficientnet/config.py
echo "Running eval, bs=16"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 16,self.eval_batch_size = 32,' torchbenchmark/models/timm_efficientnet/config.py
echo "Running eval, bs=32"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 32,self.eval_batch_size = 64,' torchbenchmark/models/timm_efficientnet/config.py
echo "Running eval, bs=64"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 64,self.eval_batch_size = 128,' torchbenchmark/models/timm_efficientnet/config.py
echo "Running eval, bs=128"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 128,self.eval_batch_size = 256,' torchbenchmark/models/timm_efficientnet/config.py
echo "Running eval, bs=256"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 256,self.eval_batch_size = 512,' torchbenchmark/models/timm_efficientnet/config.py
echo "Running eval, bs=512"
python run.py timm_efficientnet -t eval -d cuda
sed -i 's,self.eval_batch_size = 512,self.eval_batch_size = 1,' torchbenchmark/models/timm_efficientnet/config.py


