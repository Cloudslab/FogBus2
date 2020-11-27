# Base
FROM linuxserver/nginx:09f3a698-ls105 

# JAVA8
RUN apk add --no-cache openjdk8

# Ports
EXPOSE 80 

# Run FogBus
WORKDIR /config/www
CMD ["sh","-c","java -jar MasterInterface.jar"]
