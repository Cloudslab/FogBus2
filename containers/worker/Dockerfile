# Builder
FROM newdeveloper/apache-php:24-04-2020

# JAVA8
RUN apt-get install openjdk-8-jre-headless -y

# Expose port
EXPOSE 80

# Apache
RUN echo "ServerName 127.0.0.1" >> /etc/apache2/apache2.conf
RUN service apache2 restart

# Run FogBus
WORKDIR /var/www/html/
CMD ["sh","-c","service apache2 restart && java -jar WorkerInterface.jar"]
