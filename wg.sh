#! /bin/sh
# first arg is the vpn ip 
# second arg is the port that wg needs for other peers to connect
set -e

wg genkey > wireguardPrivate
ip link add wg0 type wireguard
ip addr add $1/24 dev wg0
wg set wg0 private-key ./wireguardPrivate
ip link set wg0 up
wg set wg0 listen-port $2
