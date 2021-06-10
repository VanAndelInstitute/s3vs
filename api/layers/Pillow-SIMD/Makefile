build-PillowSIMD:
	yum install -y python3-devel zlib libjpeg-turbo-devel lcms2-devel
	mkdir -p "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/liblcms2.so.2 "$(ARTIFACTS_DIR)/lib"
	mkdir -p "$(ARTIFACTS_DIR)/python"
	CC="cc -mavx2" pip install --force-reinstall --no-cache-dir --compile  pillow-simd --global-option="build_ext" --global-option="--enable-lcms" -t "$(ARTIFACTS_DIR)/python"