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
ADD sources/requirements.txt /workplace/requirements.txt
RUN python -m pip install -r requirements.txt --no-cache-dir

# Hostname
RUN echo "Worker" > /etc/hostname

# Run Worker
ENTRYPOINT ["python", "worker.py"]
