# Prepare Environment

The following instructions are for Ubuntu x86_64 only.
## Install Docker
**Step1**: Uninstall old versions
```shell
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
```
**Step2**: Add Docker's official GPG key
```bash
sudo apt-get update -y
sudo apt-get install ca-certificates curl gnupg -y
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```
**Step3**: Set up the stable repository.
```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
```
**Step4**: Install Docker Engine.
```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```
**Step5**: Verify that Docker Engine is installed correctly by running the hello-world image.
```bash
sudo docker run hello-world
```
**Step6**: Manage Docker as a non-root user.
```bash
sudo usermod -aG docker $USER
```
**Step7**: Logout and login again.
**Step8**: Install docker compose.
```bash
sudo apt install docker-compose -y
```

## Prepare the Network
**Step0**: Know your devices. Assume we have 6 devices, `A`, `B`,`C`,`D`,`E`, and `F`.

- `A`, `B`,and `C` have public IP and are in a local network of `$L_IP1_?`.
- `D`,`E`, and `F` do no have public IP.
- `D`,`E`, and `F` are in  a local network of `$L_IP2_?`.

|              |        A    |       B  |       C  |     D     |     E      |    F     |
|:------------:|:-----------:|:--------:|:--------:|:---------:|:----------:|:--------:|
|  Public IP   |     $P_IP_A | $P_IP_B | $P_IP_C |    NA     |     NA     |    NA    |
|   Local IP   | $L_IP1_A    | $L_IP1_B | $L_IP1_C | $L_IP2_D  |  $L_IP2_E  | $L_IP2_F |
| Wireguard IP |     |  |  |   |    |          |

**Step1**: Install Wireguard on each device.
```bash
sudo apt install wireguard -y
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```
**Step2**: Generate the private key and public key for each device. Take `A` as an example. Please run the following command on every device but replace the device name with the corresponding one.
```bash
mkdir -p A_wg_keys && wg genkey | tee A_wg_keys/A_wg_pri_key | wg pubkey > A_wg_keys/A_wg_pub_key
```
Show the keys
```bash
cat A_wg_keys/A_wg_pri_key
```
The output is `$A_WG_PRI_KEY`.
```bash
cat A_wg_keys/A_wg_pub_key
```
The output is `$A_WG_PUB_KEY`.  

**Step3.1**: Create the configuration file and run Wireguard service on `A`. Remember to replace the variables with the corresponding values.
```bash
cat <<EOF > wgA.conf
[Interface]
Address = 10.4.2.101/32
ListenPort = 51820
PrivateKey = $A_WG_PRI_KEY
SaveConfig = true

[Peer]
PublicKey = $B_WG_PUB_KEY
AllowedIPs = 10.4.2.102/32
Endpoint = $L_IP1_B:51820

[Peer]
PublicKey = $C_WG_PUB_KEY
AllowedIPs = 10.4.2.103/32
Endpoint = $L_IP1_C:51820
EOF

sudo cp wgA.conf /etc/wireguard/
sudo systemctl enable wg-quick@wgA
sudo systemctl start wg-quick@wgA
sudo wg-quick up wgA
```
**Step3.2**: Create the configuration file and run Wireguard service on `B`. Remember to replace the variables with the corresponding values.
```bash
cat <<EOF > wgB.conf
[Interface]
Address = 10.4.2.102/32
ListenPort = 51820
PrivateKey = $B_WG_PRI_KEY
SaveConfig = true

[Peer]
PublicKey = $A_WG_PUB_KEY
AllowedIPs = 10.4.2.101/32
Endpoint = $L_IP1_A:51820

[Peer]
PublicKey = $C_WG_PUB_KEY
AllowedIPs = 10.4.2.103/32
Endpoint = $L_IP1_C:51820
EOF

sudo cp wgB.conf /etc/wireguard/
sudo systemctl enable wg-quick@wgB
sudo systemctl start wg-quick@wgB
sudo wg-quick up wgB
```

**Step3.3**: Create the configuration file and run Wireguard service on `C`. Remember to replace the variables with the corresponding values.
```bash
cat <<EOF > wgC.conf
[Interface]
Address = 10.4.2.103/32
ListenPort = 51820
PrivateKey = $C_WG_PRI_KEY
SaveConfig = true

[Peer]
PublicKey = $A_WG_PUB_KEY
AllowedIPs = 10.4.2.101/32
Endpoint = $L_IP1_A:51820

[Peer]
PublicKey = $B_WG_PUB_KEY
AllowedIPs = 10.4.2.102/32
Endpoint = $L_IP1_B:51820
EOF

sudo cp wgC.conf /etc/wireguard/
sudo systemctl enable wg-quick@wgC
sudo systemctl start wg-quick@wgC
sudo wg-quick up wgC
```

Now the network becomes

|              |     A      |     B      |     C      |    D     |    E     |    F     |
|:------------:|:----------:|:----------:|:----------:|:--------:|:--------:|:--------:|
|  Public IP   |  $P_IP_A   |  $P_IP_B  |  $P_IP_C  |    NA    |    NA    |    NA    |
|   Local IP   |  $L_IP1_A  |  $L_IP1_B  |  $L_IP1_C  | $L_IP2_D | $L_IP2_E | $L_IP2_F |
| Wireguard IP | 10.4.2.101 | 10.4.2.102 | 10.4.2.103 |          |          |          |

**Step4.1**: Create the configuration file and run Wireguard service on `D`. Remember to replace the variables with the corresponding values.
```bash
cat <<EOF > wgD.conf
[Interface]
Address = 10.4.2.201/32
ListenPort = 51820
PrivateKey = $D_WG_PRI_KEY
SaveConfig = true

[Peer]
PublicKey = $A_WG_PUB_KEY
AllowedIPs = 10.4.2.101/32
Endpoint = $P_IP_A:51820

[Peer]
PublicKey = $B_WG_PUB_KEY
AllowedIPs = 10.4.2.102/32
Endpoint = $P_IP_B:51820

[Peer]
PublicKey = $C_WG_PUB_KEY
AllowedIPs = 10.4.2.103/32
Endpoint = $P_IP_C:51820

[Peer]
PublicKey = $E_WG_PUB_KEY
AllowedIPs = 10.4.2.202/32
Endpoint = $L_IP2_E:51820

[Peer]
PublicKey = $F_WG_PUB_KEY
AllowedIPs = 10.4.2.203/32
Endpoint = $L_IP2_F:51820
EOF

sudo cp wgD.conf /etc/wireguard/
sudo systemctl enable wg-quick@wgD
sudo systemctl start wg-quick@wgD
sudo wg-quick up wgD
```

**Step4.2**: Create the configuration file and run Wireguard service on `E`. Remember to replace the variables with the corresponding values.
```bash
cat <<EOF > wgE.conf
[Interface]
Address = 10.4.2.202/32
ListenPort = 51820
PrivateKey = $D_WG_PRI_KEY
SaveConfig = true

[Peer]
PublicKey = $A_WG_PUB_KEY
AllowedIPs = 10.4.2.101/32
Endpoint = $P_IP_A:51820

[Peer]
PublicKey = $B_WG_PUB_KEY
AllowedIPs = 10.4.2.102/32
Endpoint = $P_IP_B:51820

[Peer]
PublicKey = $C_WG_PUB_KEY
AllowedIPs = 10.4.2.103/32
Endpoint = $P_IP_C:51820

[Peer]
PublicKey = $D_WG_PUB_KEY
AllowedIPs = 10.4.2.201/32
Endpoint = $L_IP2_D:51820

[Peer]
PublicKey = $F_WG_PUB_KEY
AllowedIPs = 10.4.2.203/32
Endpoint = $L_IP2_F:51820
EOF

sudo cp wgE.conf /etc/wireguard/
sudo systemctl enable wg-quick@wgE
sudo systemctl start wg-quick@wgE
sudo wg-quick up wgE
```


**Step4.3**: Create the configuration file and run Wireguard service on `F`. Remember to replace the variables with the corresponding values.
```bash
cat <<EOF > wgF.conf
[Interface]
Address = 10.4.2.203/32
ListenPort = 51820
PrivateKey = $F_WG_PRI_KEY
SaveConfig = true

[Peer]
PublicKey = $A_WG_PUB_KEY
AllowedIPs = 10.4.2.101/32
Endpoint = $P_IP_A:51820

[Peer]
PublicKey = $B_WG_PUB_KEY
AllowedIPs = 10.4.2.102/32
Endpoint = $P_IP_B:51820

[Peer]
PublicKey = $C_WG_PUB_KEY
AllowedIPs = 10.4.2.103/32
Endpoint = $P_IP_C:51820

[Peer]
PublicKey = $D_WG_PUB_KEY
AllowedIPs = 10.4.2.201/32
Endpoint = $L_IP2_D:51820

[Peer]
PublicKey = $E_WG_PUB_KEY
AllowedIPs = 10.4.2.202/32
Endpoint = $L_IP2_E:51820
EOF

sudo cp wgF.conf /etc/wireguard/
sudo systemctl enable wg-quick@wgF
sudo systemctl start wg-quick@wgF
sudo wg-quick up wgF
```

Now the network becomes

|              |     A      |     B      |     C      |     D      |     E      |     F      |
|:------------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|
|  Public IP   |  $P_IP_A   | $P_IP_B    |  $P_IP_C   |     NA     |     NA     |     NA     |
|   Local IP   |  $L_IP1_A  |  $L_IP1_B  |  $L_IP1_C  |  $L_IP2_D  |  $L_IP2_E  |  $L_IP2_F  |
| Wireguard IP | 10.4.2.101 | 10.4.2.102 | 10.4.2.103 | 10.4.2.201 | 10.4.2.202 | 10.4.2.203 |


## Prepare Database on A
**step0**: Navigate to the folder of MariaDB.

```bash
git clone https://github.com/Cloudslab/FogBus2.git
cd FogBus2/containers/database/mariadb/
```

**Step1**: Run MariaDB in a Docker container.
```bash
docker run -p 3306:3306 \
            --name fogbus2-mariadb \
            -v $(pwd)/mysql:/var/lib/mysql \
            -e MYSQL_ROOT_PASSWORD=passwordForRoot \
            -e MYSQL_USER=fogbus2 \
            -e MYSQL_PASSWORD=passwordForRoot \
            -d mariadb:11.2.2
```
**Step2**: Create the databases from sql file.
```bash
docker run --rm -it \
           --net host \
           -e MYSQL_PWD=passwordForRoot \
           -v $(pwd)/sqlFiles:/sqlFiles/ \
           mariadb:11.2.2 \
           bash -c \
               "mariadb -h 127.0.0.1 \
                        -u root \
                        < /sqlFiles/allDatabases.sql"
```

## Run FogBus2

### Run RemoteLogger, Master, and Actor on A
**step0**: Navigate to the folder of remote logger.

```bash
git clone https://github.com/Cloudslab/FogBus2.git
cd FogBus2/containers/remoteLogger
```
**step1**: Run RemoteLogger in a Docker container.
```bash
docker pull cloudslab/fogbus2-remote_logger
docker-compose run \
                  --rm \
                  --name RemoteLogger \
                  fogbus2-remote_logger \
                  --bindIP 10.4.2.101 \
                  --bindPort 5000 \
                  --containerName RemoteLogger
```

**step2**: Run Master in a Docker container.
```bash
cd FogBus2/containers/master
docker pull cloudslab/fogbus2-master
docker-compose run \
                  --rm \
                  --name Master \
                  fogbus2-master \
                  --bindIP 10.4.2.101 \
                  --bindPort 5001 \
                  --containerName Master \
                  --remoteLoggerIP 10.4.2.101 \
                  --remoteLoggerPort 5000
```

**step2**: Run Actor in a Docker container.
```bash
cd FogBus2/containers/actor
docker pull cloudslab/fogbus2-actor
docker-compose run \
                  --rm \
                  --name Actor \
                  fogbus2-actor \
                  --bindIP REPLACE_IP
                  --bindPort 50000 \
                  --containerName Actor \
                  --remoteLoggerIP REPLACE_IP
                  --remoteLoggerPort 5000 \
                  --masterIP REPLACE_IP
                  --masterPort 5001
```

### Run Actor on B
**step0**: Navigate to the folder of remote logger.

```bash
git clone https://github.com/Cloudslab/FogBus2.git
cd FogBus2/containers/actor
```

**step1**: Run Actor in a Docker container.
```bash
docker pull cloudslab/fogbus2-actor
docker-compose run \
                  --rm \
                  --name Actor \
                  fogbus2-actor \
                  --bindIP 10.4.2.102 \
                  --bindPort 50000 \
                  --containerName Actor \
                  --remoteLoggerIP 10.4.2.101 \
                  --remoteLoggerPort 5000 \
                  --masterIP 10.4.2.101 \
                  --masterPort 5001
```

### Run Actor on C
**step0**: Navigate to the folder of remote logger.

```bash
git clone https://github.com/Cloudslab/FogBus2.git
cd FogBus2/containers/actor
```

**step1**: Run Actor in a Docker container.
```bash
docker pull cloudslab/fogbus2-actor
docker-compose run \
                  --rm \
                  --name Actor \
                  fogbus2-actor \
                  --bindIP 10.4.2.103 \
                  --bindPort 50000 \
                  --containerName Actor \
                  --remoteLoggerIP 10.4.2.101 \
                  --remoteLoggerPort 5000 \
                  --masterIP 10.4.2.101 \
                  --masterPort 5001
```
```shell
docker pull cloudslab/fogbus2-user
docker-compose run \
                    --rm \
                    --name UserDiabetesPrediction \
                    -v $(pwd)/:/data \
                    fogbus2-user \
                        --bindIP REPLACE_IP
                        --bindPort 50101 \
                        --containerName UserDiabetesPrediction \
                        --remoteLoggerIP REPLACE_IP
                        --remoteLoggerPort 5000 \
                        --masterIP REPLACE_IP
                        --masterPort 5001 \
                            --applicationName DiabetesPrediction \
                            --csvPath /data/diabetes_PIMA.csv
```
