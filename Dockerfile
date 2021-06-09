FROM continuumio/miniconda3:4.9.2-alpine

WORKDIR "/home"

# Install the app dependencies into the base conda environment so we
# don't need to activate a conda environment when running.
# Need git to install harmony-service library from github
RUN apk update
RUN apk add git
COPY environment.yml .
RUN conda env update --file environment.yml -n base

# This is below the preceding layer to prevent Docker from rebuilding the
# previous layer (forcing a conda reload of dependencies) whenever the
# status of a local service library changes
ARG service_lib_dir=NO_SUCH_DIR

# Install a local harmony-service-lib-py if we have one
COPY deps ./deps/
RUN if [ -d deps/${service_lib_dir} ]; then echo "Installing from local copy of harmony-service-lib"; pip install -e deps/${service_lib_dir}; fi

# Copy the app. This step is last so that Docker can cache layers for the steps above
COPY . .

ENTRYPOINT ["python", "-m", "harmony_service_example"]