build-libdmtx:
	yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
	yum install -y libdmtx
	mkdir -p "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libdmtx.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libdmtx.so.0 "$(ARTIFACTS_DIR)/lib/libdmtx.so"

	# the next few lines are because ld is broken in the Lambda python3.8+ runtime image 
	cp /usr/lib64/libbfd-2.29.1-30.amzn2.so "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libopcodes-2.29.1-30.amzn2.so "$(ARTIFACTS_DIR)/lib"
	mkdir -p "$(ARTIFACTS_DIR)/bin"
	cp /usr/bin/ld.bfd "$(ARTIFACTS_DIR)/bin/ld"
	cp /usr/bin/objdump "$(ARTIFACTS_DIR)/bin"

