.PHONY: all fetch build check demo clean
all: build
fetch:
	python3 scripts/build.py --fetch-only
build:
	python3 scripts/build.py
check: build
	python3 scripts/check.py
demo: build
	mkdir -p build/demo
	cd build/demo && ../../alg -su ../../examples/hello.a68 && ../../ago
clean:
	rm -rf build
