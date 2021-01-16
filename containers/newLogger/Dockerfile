# Base
FROM python:3.9.1-alpine3.12
WORKDIR /workplace

# Hostname
RUN echo 'RemoteLogger' > /etc/hostname

# Ports
EXPOSE 5001

# Dependencies
RUN apk add --no-cache make automake gcc g++ subversion
ADD requirements.txt /workplace/requirements.txt
RUN python -m pip install -r requirements.txt

# Run RemoteLogger
CMD ["sh","-c","python remoteLogger.py"]
