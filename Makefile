.PHONY: test
SHELL := /bin/bash

run:
	@ ./canary.py batch canary.json

build:
	@ docker build . --tag canary > /dev/null 2>&1

test: build
	@ docker run --rm -v ${PWD}:/python canary python3 test_canary.py --verbose --buffer

run_docker: build
	@ docker run --rm -v ${PWD}:/python canary ./canary.py batch canary.json

format: build
	@ docker run --rm -v ${PWD}:/python canary black --verbose --line-length 100 .

lint: build
	@ docker run --rm -v ${PWD}:/python canary black --diff --check --verbose --line-length 100 .
	@ docker run --rm -v ${PWD}:/python canary flake8 --verbose --max-line-length=100

validate: test lint
