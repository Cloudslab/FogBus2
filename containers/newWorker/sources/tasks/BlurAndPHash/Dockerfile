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
RUN cd /workplace/ \
    && curl -L "https://github.com/opencv/opencv/archive/4.5.1.zip" -o opencv.zip \
    && curl -L "https://github.com/opencv/opencv_contrib/archive/4.5.1.zip" -o opencv_contrib.zip \
    && unzip opencv.zip \
    && unzip opencv_contrib.zip \
    && rm opencv.zip opencv_contrib.zip

## Configure
RUN cd /workplace/opencv-4.5.1 \
    && mkdir -p build && cd build \
    && cmake \
        -DOPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-4.5.1/modules \
        -DBUILD_NEW_PYTHON_SUPPORT=ON \
        -DBUILD_opencv_python3=ON \
        -DHAVE_opencv_python3=ON \
        -DPYTHON_DEFAULT_EXECUTABLE=$(which python) \
        -DBUILD_TESTS=OFF \
        -DWITH_FFMPEG=ON \
        ../

## Compile
RUN cd /workplace/opencv-4.5.1/build && make -j $(nproc) && make install

## Python libararies
ADD taskSample/requirements.txt /workplace/requirements.txt
RUN python -m pip install -r requirements.txt --no-cache-dir

## Copy files
ADD ./taskSample/*.py /workplace/

# Hostname
RUN echo "BlurAndPHash" > /etc/hostname

# Run BlurAndPHash
ENTRYPOINT ["python", "taskHandler.py"]
