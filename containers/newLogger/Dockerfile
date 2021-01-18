# Base
FROM python:3.9.1-alpine3.12
WORKDIR /workplace

# Hostname
RUN echo 'RemoteLogger' > /etc/hostname

# Dependencies
RUN apk add --no-cache make automake gcc g++ subversion
ADD sources/requirements.txt /workplace/requirements.txt
RUN python -m pip install -r requirements.txt --no-cache-dir

# Ports
EXPOSE 5001

# Run RemoteLogger
CMD ["sh","-c","python remoteLogger.py"]
