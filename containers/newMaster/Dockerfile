# Base
FROM python:3.9.1-alpine3.12

# Hostname
RUN echo 'Master' > /etc/hostname

# Ports
EXPOSE 5000

# Dependencies
RUN apk add --no-cache make automake gcc g++ subversion
RUN python -m pip -r requirements.txt

# Run RemoteLogger
WORKDIR /workplace
CMD ["sh","-c","python master.py"]
