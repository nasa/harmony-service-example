# harmony-gdal

A demonstration of a subsetter capability to be used with Harmomy.

## Prerequisites

For building & pushing the image locally:

1. [Docker](https://www.docker.com/get-started)

For local development:

1. [pyenv](https://github.com/pyenv/pyenv)
2. [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

## Local Development

### Install dependencies

1. Install & use miniconda:

        $ pyenv install miniconda3-4.7.12
        $ pyenv local miniconda3-4.7.12

2. Create and activate a conda environment containing the development dependencies.

   *IMPORTANT*: Activate the NASA VPN first. This project depends on the Harmony Service Library, which is installed from the Nexus artifact repository.

        $ conda env create -n hgdal
        $ pyenv activate hgdal

        # To update pyenv's 'shims' for executables
        $ pyenv rehash  

### Run unit tests:

        # Run the tests once:
        $ pytest --ignore deps

        # Run the tests continuously in watch mode:
        $ ptw -c --ignore deps

### Developing with a local version of the Harmony Service Library

You may want to test Harmony GDAL with an unreleased version of the Harmony Service Library.  This might be someone else's feature or bug-fix branch, or perhaps your own local changes. If you haven't already, clone the Harmony Service Lib and switch to an unreleased branch or make your local changes. Typically this clone would be in a sibling directory of Harmony GDAL:

        $ git clone https://git.earthdata.nasa.gov/projects/HARMONY/repos/harmony-service-lib-py/browse ../harmony-service-lib-py

Then install it into your conda environment in development mode. Subsequent changes to the Harmony Service Library will be reflected immediately without need to install it again:

        $ pip install -e ../harmony-service-lib

## Building & deploying the Docker image

1a. Build the Docker image (installs Harmony Service Library from its remote artifact repository):

        $ bin/build-image

1b. If you'd like the Docker image to include a local version of the Harmony Service Library, set the `LOCAL_HSLP` environment variable to its location and build the image as in 1a:

        $ LOCAL_HSLP=../harmony-service-lib-py bin/build-image

2. (Optional) Deploy (publish) the Docker image to Amazon ECR:

        $ bin/push-image

### Building from Dev Container

If you plan to build the Docker image from a container, in addition to the above instructions, you'll want to create a .env file and populate it with the following:

```
# Harmony-GDAL Environment Variables

# Set to 'true' if running Docker in Docker and the docker daemon is somewhere other than the current context
DIND=true

# Indicates where docker commands should find the docker daemon
DOCKER_DAEMON_ADDR=host.docker.internal:2375
```

## CI

The project has a [Bamboo CI job](https://ci.earthdata.nasa.gov/browse/HARMONY-HG) running
in the Earthdata Bamboo environment.
