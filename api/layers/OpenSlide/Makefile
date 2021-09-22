build-OpenSlide:
	yum install -y libjpeg-turbo-devel openjpeg2-devel libtiff-devel cairo-devel gdk-pixbuf2-devel sqlite-devel libxml2-devel libcurl-devel
	mkdir -p "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libcairo.so.2 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libxml2.so.2 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libopenjp2.so.7 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libtiff.so.5 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libpng15.so.15 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libgdk_pixbuf-2.0.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libjpeg.so.62 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libEGL.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libfontconfig.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libfreetype.so.6 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libglib-2.0.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libgmodule-2.0.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libgobject-2.0.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libgthread-2.0.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libgio-2.0.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libmount.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libpixman-1.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libxcb-shm.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libxcb.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libxcb-render.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libXrender.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libX11.so.6 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libXext.so.6 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libGL.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/liblzma.so.5 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libjbig.so.2.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libblkid.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libuuid.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libexpat.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libbz2.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libGLdispatch.so.0  "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libXau.so.6 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libGLX.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libcurl.so.4 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libnghttp2.so.14 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libidn2.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libssh2.so.1 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libldap-2.4.so.2 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/liblber-2.4.so.2 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libunistring.so.0 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libsasl2.so.3 "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libssl3.so "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libsmime3.so "$(ARTIFACTS_DIR)/lib"
	cp /usr/lib64/libnss3.so "$(ARTIFACTS_DIR)/lib"

	yum install -y cmake3
	git clone https://github.com/json-c/json-c.git
	mkdir json-c-build
	cd json-c-build \
	&& cmake3 -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE="release" ../json-c \
	&& make \
	&& make install
	cp /usr/lib64/libjson-c.so.5 "$(ARTIFACTS_DIR)/lib"

	curl -o gdal.zip -L https://github.com/VanAndelInstitute/gdal-vsi/archive/master.zip
	unzip gdal.zip
	cd gdal-vsi-master/gdal \
	&& ./configure --with-proj=no --disable-all-optional-drivers --prefix=/usr --libdir=/usr/lib64 \
	&& make -j8 \
	&& make install
	cp /usr/lib64/libgdal.so.29 "$(ARTIFACTS_DIR)/lib"

	git clone https://github.com/VanAndelInstitute/openslide.git
	cd openslide \
	&& autoreconf -i \
	&& ./configure --prefix=/usr --libdir=/usr/lib64 \
	&& make \
	&& make install
	cp /usr/lib64/libopenslide.so.0 "$(ARTIFACTS_DIR)/lib"

	pip install openslide-python --no-deps -t "$(ARTIFACTS_DIR)/python"