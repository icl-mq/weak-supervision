# Weak Supervision

[Description](#description)

This repository contains companion code for the paper "". If you use these codes in your research, we would appreciate if you cite the following paper:

[Requirements](#requirements)

The code was tested with Python 3.8.10 on Ubuntu 20.04. In order to install we recommend use of a virtual environment. In order to avoid dependency issues with recent packages, using a recent version of pip is also highly recommended. We used the following steps to create an environment:

```terminal
python3 -m venv --copies .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools
pip install wheel
```

Now you can install the dependencies, and finally the weak-supervision package

```terminal
pip install -r requirements.txt
pip install -e .
```

[Example](#example)

An example notebook can be found in experiments/ebu3b - this contains a step by step example of our experiment.