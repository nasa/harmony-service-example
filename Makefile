.PHONY: build-image push-image test test-watch install

install:
	conda-env update --file environment-dev.yml

build-image:
	LOCAL_SVCLIB_DIR=${LOCAL_SVCLIB_DIR} bin/build-image

push-image:
	bin/push-image

test:
	pytest --ignore deps

test-watch:
	ptw -c --ignore deps