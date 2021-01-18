# Base
FROM python:3.9.1-alpine3.12
WORKDIR /workplace

## Dependencies
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add --no-cache \
    build-base clang clang-dev ninja cmake ffmpeg-dev \
    freetype-dev g++ jpeg-dev lcms2-dev libffi-dev \
    libgcc libxml2-dev libxslt-dev linux-headers \
    make musl musl-dev openjpeg-dev openssl-dev \
    zlib-dev curl freetype gcc6 jpeg libjpeg \
    openjpeg tesseract-ocr zlib unzip openjpeg-tools
RUN python -m pip install numpy --no-cache-dir

## OpenCV Source Code
RUN mkdir /workplace/opencv &&  cd /workplace/opencv \
    && curl -L "https://github.com/opencv/opencv/archive/master.zip" -o opencv.zip \
    && curl -L "https://github.com/opencv/opencv_contrib/archive/master.zip" -o opencv_contrib.zip \
    && unzip opencv.zip \
    && unzip opencv_contrib.zip \
    && rm opencv.zip opencv_contrib.zip

## Configure
RUN cd /workplace/opencv \
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
RUN cd /workplace/opencv/build && make -j $(nproc) && make install

## Python libararies
ADD requirements.txt /workplace/requirements.txt
RUN python -m pip install -r requirements.txt --no-cache-dir

# Hostname
RUN echo "EyeDetection" > /etc/hostname

# Run EyeDetection
ENTRYPOINT ["python", "worker.py"]
