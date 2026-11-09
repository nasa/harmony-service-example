# ---- Build stage: resolve the conda environment ----
# micromamba is only used to build the environment; neither it nor conda
# end up in the final image.
FROM mambaorg/micromamba:2-debian13-slim AS build

USER root

COPY environment.yml /tmp/environment.yml
RUN micromamba create --yes --prefix /opt/env --file /tmp/environment.yml && \
    micromamba clean --all --yes

# This is below the preceding layer to prevent Docker from rebuilding the
# previous layer (forcing a conda reload of dependencies) whenever the
# status of a local service library changes
ARG service_lib_dir=NO_SUCH_DIR

# Install a local harmony-service-lib-py if we have one
COPY deps /tmp/deps/
RUN if [ -d "/tmp/deps/${service_lib_dir}" ]; then \
      echo "Installing from local copy of harmony-service-lib"; \
      /opt/env/bin/pip install --no-cache-dir "/tmp/deps/${service_lib_dir}"; \
    else \
      echo "No local harmony-service-lib found, skipping install."; \
    fi && \
    find /opt/env -name '__pycache__' -type d -prune -exec rm -rf {} + && \
    rm -rf /opt/env/pkgs

# ---- Runtime stage: minimal glibc-based Wolfi plus the environment only ----
# Wolfi is a rolling, glibc-based distro that ships security fixes quickly.
# Chainguard's free tier only publishes `latest`, so pin by digest for
# reproducible builds; bump the digest to pick up a newer base.
FROM cgr.dev/chainguard/wolfi-base:latest@sha256:24f549a7fcace88e69b9557941168c74645688ecc4acf7fb6d734a6b74e9019d

USER root

# Pick up any OS fixes released since the pinned base was published, then
# strip setuid/setgid bits (the service never needs privilege escalation).
# busybox in wolfi-base provides the rm/mkdir/cp/mv the service shells out to.
RUN apk upgrade --no-cache && \
    find / -xdev -perm /6000 -type f -exec chmod a-s {} +

# Same path as the build stage so script shebangs (e.g. gdal_merge.py) resolve
COPY --from=build /opt/env /opt/env

ENV PATH=/opt/env/bin:$PATH \
    PROJ_LIB=/opt/env/share/proj \
    GDAL_DATA=/opt/env/share/gdal \
    PIP_NO_CACHE_DIR=1

WORKDIR "/home"

# Copy the app. This step is last so that Docker can cache layers for the steps above
COPY harmony_service_example ./harmony_service_example

ENTRYPOINT ["python", "-m", "harmony_service_example"]
