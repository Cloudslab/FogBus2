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
    jpeg-dev zlib-dev

RUN python -m pip install -U --force-reinstall pip

RUN python -m \
    pip install --no-cache-dir \
    numpy psutil GPUtil docker \
    pymoo autograd

RUN apk add --no-cache \
    iperf3 pythonping

RUN python -m \
    pip install --no-cache-dir \
    iperf3

ADD ./sources /workplace

# Hostname
RUN echo "Master" > /etc/hostname

# Ports
EXPOSE 5000

# Run Master
ENTRYPOINT ["python", "-u", "master.py"]
