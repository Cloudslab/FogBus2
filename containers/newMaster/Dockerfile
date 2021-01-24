# Base
FROM python:3.9.1-alpine3.12
WORKDIR /workplace

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories

## Dependencies
RUN apk add --no-cache \
    make automake gcc g++ subversion \
    linux-headers
RUN apk add --no-cache \
    gfortran openblas-dev lapack-dev \
    zlib
ADD sources/requirements.txt /workplace/requirements.txt
RUN python -m pip install -r requirements.txt --no-cache-dir

# Hostname
RUN echo "Master" > /etc/hostname

# Ports
EXPOSE 5000

# Run Master
ENTRYPOINT ["python", "master.py"]
