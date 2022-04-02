# Base
FROM python:3.9-alpine3.14 as base
FROM base as builder

## Dependencies
RUN apk update
RUN apk add --no-cache \
    build-base clang clang-dev ninja cmake ffmpeg-dev \
    freetype-dev g++ jpeg-dev lcms2-dev libffi-dev \
    libgcc libxml2-dev libxslt-dev linux-headers \
    make musl musl-dev openjpeg-dev openssl-dev \
    zlib-dev curl freetype gcc6 jpeg libjpeg \
    openjpeg tesseract-ocr zlib unzip openjpeg-tools

RUN python -m pip install --retries 100 --default-timeout=600  --no-cache-dir --upgrade pip
RUN python -m pip install --retries 100 --default-timeout=600  numpy==1.22.2 --no-cache-dir

## OpenCV Source Code
WORKDIR /workplace
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

RUN cd /workplace/opencv-4.5.1/build && make -j $(( $(nproc) - 1 ))
RUN cd /workplace/opencv-4.5.1/build && make install

## Python libraries
COPY ./sources/requirements.txt /install/requirements.txt
RUN python -m pip install --retries 100 --default-timeout=600  \
    --prefix=/install \
    --no-cache-dir \
    -r /install/requirements.txt

## Copy files
FROM base
COPY --from=builder /install /usr/local
COPY ./sources/ /workplace

## Install opencv
COPY  --from=builder /usr/local/ /usr/local/
COPY --from=builder /usr/lib/ /usr/lib/

# Hostname
RUN echo "OCR" > /etc/hostname

# Run OCR
WORKDIR /workplace
ENTRYPOINT ["python", "taskExecutor.py"]
