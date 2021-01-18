# Base
FROM python:3.9.1-alpine3.12
WORKDIR /workplace

# Hostname
RUN echo "Master" > /etc/hostname

## Dependencies
RUN apk add --no-cache \
    make automake gcc g++ subversion \
    linux-headers
ADD requirements.txt /workplace/requirements.txt
RUN python -m pip install -r requirements.txt

# Ports
EXPOSE 5000

# Run Master
ENTRYPOINT ["python", "master.py"]
