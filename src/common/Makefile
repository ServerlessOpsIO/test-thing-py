build-CommonLayer:
	python3.13 ./setup.py build
	pip3.13 wheel -w tmp -e .
	mkdir $(ARTIFACTS_DIR)/python
	pip3.13 install tmp/common-* --target $(ARTIFACTS_DIR)/python/

