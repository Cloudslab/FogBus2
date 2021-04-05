import os

from dotenv import dotenv_values as dotenvValues

currPath = os.path.abspath(os.path.curdir)

# Get available ips from config file
networkEnvPath = os.path.join(currPath, '../../config/network.env')
networkEnvPath = os.path.abspath(networkEnvPath)
networkEnv = dotenvValues(networkEnvPath)
wgNet = networkEnv['WG_NET']
wgMask = wgNet[wgNet.find('/'):]
wgPort = int(networkEnv['WG_PORT'])
from ipaddress import ip_network

availableIPs = list(ip_network(wgNet).hosts())
print('[*] Read available ips: %s from %s' % (wgNet, networkEnvPath))

# read hosts info
hostsEnvPath = os.path.join(currPath, '../../config/host/hostIP.csv')
hostsEnvPath = os.path.abspath(hostsEnvPath)
f = open(hostsEnvPath, 'r')
import csv

hostCSV = csv.reader(f)
hosts = {}
for hostname, ip in hostCSV:
    hosts[hostname] = ip
del hosts['hostname']
f.close()
print("[*] Read %d hosts from %s" % (len(hosts), hostsEnvPath))
from pprint import pprint

pprint(hosts)

# Generate wireguard config

wgConfigPath = os.path.join(currPath, '../../output/wireguardConfg')
wgConfigPath = os.path.abspath(wgConfigPath)

import subprocess

# generate wireguard public and private key
# forwarding = '# IP forwarding\n' \
#              'PreUp = sysctl -w net.ipv4.ip_forward=1\n'
forwarding = '# IP forwarding\n' \
             'PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat ' \
             '-A POSTROUTING -o ens3 -j MASQUERADE\n' \
             'PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat ' \
             '-D POSTROUTING -o ens3 -j MASQUERADE\n'
print('=' * 42)
print('hostname WireguardIP')
interfaces = {}
peers = {}

for i, (hostname, hostPubIp) in enumerate(hosts.items()):
    hostOutPath = os.path.join(wgConfigPath, hostname)
    os.system('mkdir -p %s' % hostOutPath)

    hostWGPrivateKeyPath = os.path.join(hostOutPath, 'private')
    os.system('touch %s && chmod 600 %s' % (
        hostWGPrivateKeyPath, hostWGPrivateKeyPath))
    os.system('wg genkey > %s' % hostWGPrivateKeyPath)
    privateKey = subprocess.check_output(['cat', hostWGPrivateKeyPath]).decode(
        "utf-8")[:-1]

    hostWGPublicKeyPath = os.path.join(hostOutPath, 'public')
    os.system(
        'wg pubkey < %s > %s' % (hostWGPrivateKeyPath, hostWGPublicKeyPath))
    pubKey = subprocess.check_output(['cat', hostWGPublicKeyPath]).decode(
        "utf-8")[:-1]
    wgIP = availableIPs[i]
    print(hostname, wgIP)
    interface = '[Interface]\n' \
                'PrivateKey = %s\n' % privateKey + \
                'Address = %s/24\n' % wgIP + \
                'ListenPort = %d\n' % wgPort
    interfaces[hostname] = interface
    peer = '[Peer]\n' \
           '# %s\n' % hostname + \
           'PublicKey = %s\n' % pubKey
    if hostPubIp != '':
        peer += 'Endpoint = %s:%d\n' % (hostPubIp, wgPort)
    # peer += 'AllowedIPs = %s%s\n' % (wgIP, wgMask)
    peer += 'AllowedIPs = %s/32\n' % wgIP
    peer += 'PersistentKeepalive = 15\n'
    peers[hostname] = peer

print('[!] Do you want to generate wireguard configs? (y/n): ')
doGenerate = input()

configs = {}
for hostname, hostPubIp in hosts.items():
    hostOutPath = os.path.join(wgConfigPath, hostname)
    hostConfigPath = os.path.join(hostOutPath, 'wg0.conf')
    configs[hostname] = hostConfigPath

if doGenerate == 'y':
    print('[*] Generating ...')
    # generate configs
    print('=' * 42)
    for hostname, hostPubIp in hosts.items():
        hostConfigPath = configs[hostname]
        f = open(hostConfigPath, 'w+')
        f.write('# /etc/wireguard/wg0.conf\n')
        f.write('# *** Automatically Generated ***\n')
        f.write('# *** For %s Only ***\n\n' % hostname)
        f.write(interfaces[hostname] + '\n')
        # f.write(forwarding + '\n')

        for peerHostname in hosts:
            if peerHostname == hostname:
                continue
            f.write(peers[peerHostname] + '\n')
        f.close()
        print('[*] Generated Wireguard config for %s: %s ' % (hostname,
                                                              hostConfigPath))
    print('=' * 42)
    print('[!] Copy configs above to /etc/wireguard/wg0.conf of each host, '
          'respectively.')
else:
    print('[*] Skip generating.')

print('[!] Copy Wireguard config file to each host? (y/n):')
doCopy = input()
if doCopy == 'y':
    for hostname, hostPubIp in hosts.items():
        print('[~] %s' % hostname)
        os.system('scp %s %s:' % (configs[hostname], hostname))

print('[!] Configure for you? (y/n):')
i = input()
if i != 'y':
    print('[*] Bye.')
    exit(0)

print('[!] Are all the hosts running ubuntu? (y/n):')
i = input()
if i != 'y':
    print('[*] Make sure they are ubuntu. Bye.')
    exit(0)

print('[*] Configuring ...')
print('[!] Setup firewalld? (y/n):')
setupFWD = input()
for hostname, hostPubIp in hosts.items():
    if hostname == 'laptop':
        continue
    if setupFWD == 'y':
        os.system('ssh %s '
                  '"sudo dpkg --remove --force-remove-reinstreq firewalld'
                  ' ; sudo apt reinstall wireguard -y'
                  ' && sudo apt install firewalld -y'
                  ' && sudo firewall-cmd --permanent --zone=public'
                  ' --add-port=22/tcp'
                  ' && sudo firewall-cmd --permanent --zone=public'
                  ' --add-port=22/tcp'
                  ' --add-port=53/tcp'
                  ' --add-port=3306/tcp'
                  ' --add-port=4999/udp'
                  ' --add-port=5000-5010/tcp'
                  ' --add-port=5000-60000/tcp'
                  ' && sudo firewall-cmd --reload'
                  ' ; sudo firewall-cmd --state'
                  ' ; sudo firewall-cmd --list-ports'
                  ' && sudo systemctl enable firewalld'
                  ' && sudo sysctl -w net.ipv4.ip_forward=1'
                  ' && sudo wg-quick down /etc/wireguard/wg0.conf'
                  ' ; sudo wg-quick up /etc/wireguard/wg0.conf"' % hostname)
    else:
        os.system('ssh %s '
                  '"sudo cp ~/wg0.conf /etc/wireguard/wg0.conf'
                  ' && sudo wg-quick down /etc/wireguard/wg0.conf'
                  ' ; sudo wg-quick up /etc/wireguard/wg0.conf"' % hostname)
    print('[*] %s done.' % hostname)
print('[*] Script finished.')
