FROM continuumio/miniconda3:4.7.12

WORKDIR "/home"

# Install a local harmony-service-lib-py if we have one
COPY deps ./deps/
RUN if [ -d deps/harmony-service-lib-py ]; then pip3 install deps/harmony-service-lib-py; fi

# Install the app dependencies into the base conda environment so we
# don't need to activate a conda environment when running.
COPY environment.yml .
RUN conda env update --file environment.yml -n base

# Copy the app. This step is last so that Docker can cache layers for the steps above
COPY . .

# TODO - @James, I think we can either get rid of these four lines altogether, or we should move them into the README, script, or makefile. If we do keep them they probably need some tweaking...

# To run locally during dev, build the image and run, e.g.:
# docker run --rm -it -e ENV=dev -v $(pwd):/home harmony/gdal --harmony-action invoke --harmony-input "$(cat ../harmony/example/service-operation.json)"
# Or if also working on harmony-service-lib-py in a peered directory:
# docker run --rm -it -e ENV=dev -v $(pwd):/home -v $(dirname $(pwd))/harmony-service-lib-py:/home/deps/harmony harmony/gdal --harmony-action invoke --harmony-input "$(cat ../harmony/example/service-operation.json)"

ENTRYPOINT ["python", "-m", "harmony_gdal"]
