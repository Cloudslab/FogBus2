# Base
FROM python:3.7.9-alpine3.12

# OpenCV 
## Dependencies
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add --no-cache \
    build-base clang clang-dev ninja cmake ffmpeg-dev \
    freetype-dev g++ jpeg-dev lcms2-dev libffi-dev \
    libgcc libxml2-dev libxslt-dev linux-headers \
    make musl musl-dev openjpeg-dev openssl-dev \
    zlib-dev curl freetype gcc6 jpeg libjpeg \
    openjpeg tesseract-ocr zlib unzip openjpeg-tools
RUN pip install numpy

## OpenCV Source Code  
RUN cd /tmp \
    && curl -L "https://github.com/opencv/opencv/archive/master.zip" -o opencv.zip \
    && curl -L "https://github.com/opencv/opencv_contrib/archive/master.zip" -o opencv_contrib.zip \
    && unzip opencv.zip \ 
    && unzip opencv_contrib.zip 

## Configure
RUN cd /tmp/ \
    && mkdir -p build && cd build \
    && cmake \ 
        -DOPENCV_EXTRA_MODULES_PATH=../opencv_contrib-master/modules \
        -DBUILD_NEW_PYTHON_SUPPORT=ON \
        -DBUILD_opencv_python3=ON \
        -DHAVE_opencv_python3=ON \
        -DPYTHON_DEFAULT_EXECUTABLE=$(which python) \
        -DBUILD_TESTS=OFF \
        -DWITH_FFMPEG=ON \
        ../opencv-master

## Compile
RUN cd /tmp/build && make -j $(nproc) && make install

# Dependencies
RUN pip install pytesseract editdistance

# Clean cache
RUN rm -rf ~/.cache/ /tmp/*.zip /tmp/opencv_contrib-master /tmp/opencv-master

WORKDIR /workplace 

ENTRYPOINT ["python", "run.py"]
