# Base
FROM python:3.9.1-alpine3.12
WORKDIR /workplace

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories

## Dependencies
RUN apk add --no-cache \
    make automake gcc g++ subversion \
    linux-headers
ADD sources/requirements.txt /workplace/requirements.txt
RUN python -m \
    pip install --no-cache-dir \
    numpy psutil GPUtil docker

RUN python -m \
    iperf3

# Hostname
RUN echo "RemoteLogger" > /etc/hostname

# Ports
EXPOSE 5001

# Run RemoteLogger
ENTRYPOINT ["python", "remoteLogger.py"]
