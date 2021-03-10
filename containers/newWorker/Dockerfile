# Base
FROM python:3.9.1-alpine3.12
WORKDIR /workplace

## Dependencies
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add --no-cache \
    make automake gcc g++ subversion \
    linux-headers

# Docker
RUN apk add --no-cache docker docker-compose

## Python libararies
RUN python -m \
    pip install --no-cache-dir \
    numpy psutil GPUtil docker

RUN apk add --no-cache \
    gfortran openblas-dev lapack-dev \
    jpeg-dev zlib-dev

RUN python -m \
    pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pymoo

# Hostname
RUN echo "Worker" > /etc/hostname

# Run Worker
ENTRYPOINT ["python", "worker.py"]
