#!/bin/bash

echo "[1] Oprire NetworkManager & wpa_supplicant..."
sudo systemctl stop NetworkManager
sudo systemctl stop wpa_supplicant
sudo killall wpa_supplicant 2>/dev/null

echo "[2] Curățare IP & setare static pe wlan0..."
sudo ip addr flush dev wlan0
sudo ip addr add 192.168.4.1/24 dev wlan0

echo "[2.1] Setare IP static pe eth0..."
sudo ip addr flush dev eth0
sudo ip addr add 192.168.5.1/24 dev eth0

echo "[3] Repornire servicii AP (dnsmasq + hostapd)..."
sudo systemctl restart dnsmasq
sudo systemctl restart hostapd

echo "[4] Verificare hostapd..."
sudo systemctl status hostapd | tail -n 10

echo "[✔] Rețeaua 'Pi_Network' ar trebui să fie activă acum!"
