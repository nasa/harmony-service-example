FROM continuumio/miniconda3:4.7.12

ARG service_lib_dir=NO_SUCH_DIR

WORKDIR "/home"

# Install the app dependencies into the base conda environment so we
# don't need to activate a conda environment when running.
COPY environment.yml .
# RUN conda env update --file environment.yml -n base
RUN conda env update --file environment.yml -n base

# Install a local harmony-service-lib-py if we have one
COPY deps ./deps/
RUN if [ -d deps/${service_lib_dir} ]; then pip install -e deps/${service_lib_dir}; fi

# Copy the app. This step is last so that Docker can cache layers for the steps above
COPY . .

ENTRYPOINT ["python", "-m", "harmony_gdal"]
