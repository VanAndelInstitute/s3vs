build-PillowSIMD:
	yum install -y python3-devel zlib libjpeg-turbo-devel
	mkdir -p "$(ARTIFACTS_DIR)/python"
	CC="cc -mavx2" pip install --force-reinstall --no-cache-dir -t . --compile  pillow-simd -t "$(ARTIFACTS_DIR)/python"