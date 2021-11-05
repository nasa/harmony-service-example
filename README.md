# Harmony Service Example

A demonstration of a subsetter capability based on GDAL to be used with Harmony.

These instructions only apply to building and developing the service.  The example
service will be pulled automatically by Harmony from the `harmonyservices/service-example`
repository on demand.
## Prerequisites

For building & pushing the image locally:

1. [Docker](https://www.docker.com/get-started)

For local development:

1. miniconda3-4.7.12 (can be installed via pyenv)

## Local Development

### Install dependencies

1. Create a [conda virtual environment](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html):  `$ conda env create -n venv --file environment-dev.yml`
2. Activate the virtual environment: `$ conda activate venv`

### Run unit tests:

        # Run the tests once:
        $ make test

        # Run the tests continuously in watch mode:
        $ make test-watch

### Developing with a local version of the Harmony Service Library

You may want to test Harmony GDAL with an unreleased version of the Harmony Service Library.  This might be someone else's feature or bug-fix branch, or perhaps your own local changes. If you haven't already, clone the Harmony Service Lib and switch to an unreleased branch or make your local changes. Typically this clone would be in a sibling directory of Harmony GDAL:

        $ git clone https://github.com/nasa/harmony-service-lib-py ../harmony-service-lib-py

Then install it into your conda environment in development mode. Subsequent changes to the Harmony Service Library will be reflected immediately without need to install it again:

        $ pip install -e ../harmony-service-lib-py

## Building & deploying the Docker image

1. Build the Docker image (installs Harmony Service Library from PyPI):

        $ make build-image

If the Docker build does not complete and or this breaks your local Docker
environment, try increasing the memory allocated to your Docker environment.

If you'd like the Docker image to include a local version of the Harmony Service Library, set the `LOCAL_SVCLIB_DIR` environment variable to its location and build:

        $ make build-image LOCAL_SVCLIB_DIR=../harmony-service-lib-py

2. (Optional) Deploy (publish) the Docker image to Amazon ECR:

        $ make push-image

### Building from Dev Container

If you plan to build the Docker image and are running Docker in Docker, you'll also want to create a .env file and populate it with the following:

```
# Harmony-Service-Example Environment Variables

# Set to 'true' if running Docker in Docker and the docker daemon is somewhere other than the current context
DIND=true

# Indicates where docker commands should find the docker daemon
DOCKER_DAEMON_ADDR=host.docker.internal:2375
```

## CI

The project has a [Bamboo CI job](https://ci.earthdata.nasa.gov/browse/HARMONY-HG) running
in the Earthdata Bamboo environment.
