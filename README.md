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

2. Create and activate a conda environment containing the development dependencies:

        $ conda env create -n hgdal
        $ pyenv activate hgdal
        $ conda env update --file environment.yml

3. (Optional) To use an unreleased version of the `harmony-service-lib-py`, e.g., when testing changes to it, install it as a dependency from the filesystem:

        $ git clone https://git.earthdata.nasa.gov/projects/HARMONY/repos/harmony-service-lib-py/browse ../harmony-service-lib-py

### Run unit tests:

        # Run the tests once:
        $ pytest --ignore deps

        # Run the tests continuously in watch mode:
        $ ptw -c --ignore deps

## Manually building & deploying

1a. Build the Docker image (installs Harmony Service Library from its remote artifact repository):

        $ bin/build-image

1b. Build the Docker image using a local copy of the Harmony Service Library:

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
