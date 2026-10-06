FROM ghcr.io/osgeo/gdal:ubuntu-full-3.10.0


WORKDIR "/home"

# The base image's system Python is marked externally-managed (PEP 668); this
# container has no system packages to protect, so let pip install into it.
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# This image already provides GDAL and its Python bindings built against its
# own libgdal; only pip itself needs to be installed on top of it.
RUN rm -f /etc/apt/sources.list.d/apache-arrow.sources \
    && apt-get update && apt-get install -y --no-install-recommends python3-pip git \
    && rm -rf /var/lib/apt/lists/*

# Install the app dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# This is below the preceding layer to prevent Docker from rebuilding the
# previous layer (forcing a pip reinstall of dependencies) whenever the
# status of a local service library changes
ARG service_lib_dir=NO_SUCH_DIR

# Install a local harmony-service-lib-py if we have one
COPY deps ./deps/
RUN if [ -d "deps/${service_lib_dir}" ]; then \
      echo "Installing from local copy of harmony-service-lib"; \
      cd deps/${service_lib_dir} && pip3 install .; \
    else \
      echo "No local harmony-service-lib found, skipping install."; \
    fi

# Copy the app. This step is last so that Docker can cache layers for the steps above
COPY . .

ENTRYPOINT ["python3", "-m", "harmony_service_example"]