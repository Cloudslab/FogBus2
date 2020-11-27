# FogBus on RaspberryPi

## Requirements
- [Raspberry Pi devices](https://www.raspberrypi.org/products/)

## Image Preparation
Go to [Ubuntu Website](https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi) and follow the tutorial to install ubuntu on your Raspberry Pi device. 

Please use `UBUNTU DESKTOP 20.10 (RPI 4/400)`. If you don't need a desktop environment, you can also use `UBUNTU SERVER 20.10 (RPI 4/400)`.

## Docker
Please follow the [official tutorial](https://docs.docker.com/engine/install/ubuntu/) to install docker on your Raspberry Pi device.

You can also simply use the following commands,

```
sudo apt update
sudo apt remove docker docker-engine docker.io containerd runc -y
sudo apt install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository \
   "deb [arch=armhf] https://download.docker.com/linux/ubuntu \
   groovy \
   stable"
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker ubuntu
logout
```
Log in again and use `docker --version` to check the version infomation of Docker.
If everything goes fine, you should be able to run `docker run hello-world`.

## FogBus with Docker
Please move to [Container Guidelines](FogBusInContainer.md).

## FOgBus on Physical
### JAVA
1. Run the following commands to install JAVA8,
    ```
    sudo apt update
    sudo apt install openjdk-8-jre-headless -y
    ```
2. Run command `java -version` and check whether the output is like below,
    ```
    openjdk version "1.8.0_275"
    OpenJDK Runtime Environment (build 1.8.0_275-8u275-b01-0ubuntu1~18.04-b01)
    OpenJDK 64-Bit Server VM (build 25.275-b01, mixed mode)
    ```
 
### Apache2 and PHP

Run the following commands to install Apache2 and PHP,
```
sudo apt update
sudo apt install apache2 -y 
sudo apt install php libapache2-mod-php php-mysql php-xml php-zip php-gd -y
```
You will see the Apache2 default page if you visit the Raspberry Pi device's address.

#### Permissions 

In the above steps, Apache2 was installed using root user, so the permission of the default webpages folder `/var/www/html` is owned by root. 
However, this may affect the following steps because we are going to copy FogBus files to this folder. Thus, we recommend users to change the ownership of this folder and make it owned by the Apache2 default user.

Simply follow steps,
1. Get the user which runs Apache2 by running `ps aux | grep apache2`; it should be `www-data`
2. Change ownership of the folders by running `sudo chown www-data:www-data -R /var/www/html`

*Random tutorial will probably ask you to use `sudo chmod 777 -R` which gives every user all the permissions. This works but we* ***do not*** *recommend*.
### Run FogBus
Before you start, you should have [FogBus](https://github.com/Cloudslab/FogBus.git) repository cloned. Once you have it, go to root folder of FogBus,
   1. Go to `Browser-src`
   2. Copy folder `RPi` to `/var/www/html/` of your Raspberry Pi device
   3. Change the ownership of the folder. Please refer to the previous section.


#### Master
##### Firewall
Use the following commands to configure firewall rules,
```
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 3306
sudo ufw enable
```
##### MySQL

1. Install MySQL server with command `sudo apt install mysql-server -y`.
2. Configure MySQL with command `sudo mysql_secure_installation`. You can use `raspberry` as the password of root.
3. Copy file of this repository from `containers/master/data/mysql-dump/db_init.sql` to Raspberry Pi.
4. Create database,
    ```
    sudo mysql -u root -p
    mysql> CREATE DATABASE users;
    ```
5. Allow non-root user login to MySQL,
    ```
    mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'raspberry';
    mysql> FLUSH PRIVILEGES;
    mysql> exit
    ```

6. Restore database `users` with command `sudo mysql -u root -p users < /path/to/db_init.sql`.
7. Change `bind-address` in `/etc/mysql/mysql.conf.d/mysqld.cnf` to `0.0.0.0` 
8. Restart MySQL service with command `sudo service mysql restart`.

##### Configure PHP script
Edit `/var/www/html/RPi/Master/index.php` and configure database connection credential. You can locate the lines by searching key words `Database settings`.

##### Interface
Go to `/var/www/html/RPi/Master/`
1. Give all the users runnable permission with command `sudo chmod +x MasterInterface.jar`
2. Allow all the users to read and write text files with command `sudo chmod 666 *.txt`
3. Run interface with command `java -jar MasterInterface.jar`.

A FogBus Master should now run at port 80 by default.
Use your browser, open `YourRaspberriPiAddress:80/RPi/Master/` and you should be able to log in with account name `admin` when the password is also `admin`.

#### Worker
##### Firewall
Use the following commands to configure firewall rules,
```
sudo ufw allow 22
sudo ufw allow 80
```
##### Interface
Go to `/var/www/html/RPi/Worker/` and run interface with command `java -jar WorkerInterface.jar`.

A FogBus Worker should now run at port 80 by default.
Use your browser, visit it at `YourRaspberriPiAddress:80/RPi/Worker/`.
