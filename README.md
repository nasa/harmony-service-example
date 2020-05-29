# harmony-gdal

A demonstration of a subsetter capability to be used with Harmomy.

## Prerequisites

1. [pyenv](https://github.com/pyenv/pyenv)
2. [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

## Development

### Install dependencies

1. Install & use miniconda:

        $ pyenv install miniconda3-4.7.12
        $ pyenv local miniconda3-4.7.12

2. Create and activate a conda environment containing the development dependencies:

        $ conda env create -n hgdal -f environment.yml
        $ pyenv activate miniconda3-4.7.12/envs/hgdal

3. Clone `harmony-service-lib-py` locally & install it as a dependency:

        $ git clone https://git.earthdata.nasa.gov/projects/HARMONY/repos/harmony-service-lib-py/browse ../harmony-service-lib-py
        $ pip3 install ../harmony-service-lib-py/ --target deps/harmony-service-lib-py

### Run unit tests:

        # Run the tests once:
        $ pytest --ignore deps

        # Run the tests continuously in watch mode:
        $ ptw -c --ignore deps

### Manually building & deploying

1. Build the Docker image:

        $ bin/build-image

2. Deploy (publish) the Docker image to Amazon ECR:

        $ bin/push-image

## CI

The project has a [Bamboo CI job](https://ci.earthdata.nasa.gov/browse/HARMONY-HG) running
in the Earthdata Bamboo environment.
