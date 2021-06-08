FROM continuumio/miniconda3:4.9.2-alpine

WORKDIR "/home"

# Install the app dependencies into the base conda environment so we
# don't need to activate a conda environment when running.
# Need git to install harmony-service library from github
RUN apk update
RUN apk add git
COPY environment.yml .
RUN conda env update --file environment.yml -n base

# Copy the app. This step is last so that Docker can cache layers for the steps above
COPY . .

ENTRYPOINT ["python", "-m", "harmony_service_example"]
