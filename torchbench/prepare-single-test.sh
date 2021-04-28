# Compile and install pytorch
pushd $HOME/pytorch
python setup.py install

# Compile and instlal torchtext
pushd $HOME/text
python setup.py clean install

# Compile and install torchvision
pushd $HOME/vision
python setup.py install
