# harmony-gdal

A demonstration of a subsetter capability to be used with Harmomy.

## Development

### Installing dependencies - make sure to clone harmony-service-lib-py locally
```
pip3 install ../harmony-service-lib-py/ --target deps/harmony-service-lib-py
```

### Using `conda`, create a conda environment from the development dependencies:
```
conda env create -n hgdal -f environment.yml
```

### Run unit tests once or in watch-mode:
```
pytest --ignore deps
```
```
ptw -c --ignore deps
```

## Build image
```
bin/build-image
```

## Deploy image
```
bin/push-image
```
