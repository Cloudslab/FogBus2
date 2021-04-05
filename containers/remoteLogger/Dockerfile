# Base
FROM python:3.9-alpine3.14 as base

FROM base as builder

RUN mkdir /install
WORKDIR /install

## Dependencies
RUN apk add --no-cache \
    make automake gcc g++ subversion \
    linux-headers


## Python libraries
RUN python -m pip install --retries 100 --default-timeout=600  --no-cache-dir --upgrade pip
COPY ./sources/requirements.txt /install/requirements.txt
RUN python -m pip install --retries 100 --default-timeout=600  \
    --prefix=/install \
    --no-cache-dir \
    -r /install/requirements.txt

# Copy files
FROM base
COPY --from=builder /install /usr/local
COPY ./sources/ /workplace

# Hostname
RUN echo "RemoteLogger" > /etc/hostname

# Run RemoteLogger
WORKDIR /workplace
ENTRYPOINT ["python", "remoteLogger.py"]
