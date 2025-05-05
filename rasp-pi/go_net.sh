#!/bin/bash

echo "[1] Oprire Access Point (hostapd + dnsmasq)..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

echo "[2] Repornire NetworkManager..."
sudo systemctl start NetworkManager

echo "[3] Conectare la rețeaua Wi-Fi 'DigiHome'..."
nmcli dev wifi connect "DigiHome" password "tuda03tuda03"

echo "[✔] Ar trebui să ai din nou internet!"
