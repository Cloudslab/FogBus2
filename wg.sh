#! /bin/sh

set -e

wg genkey > private
ip link add wg0 type wireguard
ip addr add $1/24 dev wg0
wg set wg0 private-key ./private
ip link set wg0 up
wg set wg0 listen-port $2

