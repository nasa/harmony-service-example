# Python Versions, Virtual Environments

## (1) Multiple Versions of Python

[pyenv](https://github.com/pyenv/pyenv)  makes it easy to use multiple versions of Python
    
    $ pyenv install 3.9.1

pyenv can also install multiple versions of miniconda  (useful for conda-based projects)

    $ pyenv install miniconda3-4.7.12

Ensure that pyenv is currently using the [right version](https://github.com/pyenv/pyenv#choosing-the-python-version) of Python 
(or miniconda) after you install it

## (2) Virtual Environments

### (a) [venv](https://docs.python.org/3/library/venv.html) (built-in Python module)

- create: `$ python -m venv venv`

- activate: `$ source venv/bin/activate`

- deactivate: `$ deactivate`

### (b) [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) (works nicely with pyenv)

- create: `$ pyenv virtualenv 3.9.1 venv`

- activate: `$ pyenv activate venv`

- deactivate: `$ pyenv deactivate`

### (c) [conda](https://github.com/pyenv/pyenv-virtualenv) (if project uses conda)

- create (and install deps): `$ conda env create -n venv --file environment-file.yml`

- activate: `$ conda activate venv`

- deactivate: `$ conda deactivate`

Most shells can also be setup to automatically activate & deactivate virtual environments when cd'ing into & out of directories by using the value found in `.python-version`. This is convenient since it ensures that the correct virtualenv has been activated (and deactivated) when starting work on a project. See the pyenv and pyenv-virtualenv docs for more details.