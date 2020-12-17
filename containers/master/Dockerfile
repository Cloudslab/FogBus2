# Base
FROM linuxserver/nginx

# Alter Mirror
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories

# JAVA8
RUN apk add --no-cache openjdk8

# Ports
EXPOSE 80 

# Run FogBus
WORKDIR /config/www
CMD ["sh","-c","java -jar MasterInterface.jar"]
