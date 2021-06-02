.PHONY: install test lint test-watch build-image push-image

install:
	conda-env update --file environment-dev.yml

test:
	pytest --ignore deps

lint:
	flake8 harmony_service_example

test-watch:
	ptw -c --ignore deps

build-image:
	LOCAL_SVCLIB_DIR=${LOCAL_SVCLIB_DIR} bin/build-image

push-image:
	bin/push-image