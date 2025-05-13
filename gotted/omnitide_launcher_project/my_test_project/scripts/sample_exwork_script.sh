#!/bin/bash
echo "--- Starting Network Check ---"

echo ""
echo "[INFO] Pinging google.com (3 packets)..."
ping -c 3 google.com

echo ""
echo "[INFO] Your Local IP Configuration..."
# Try common commands, one might work
if command -v ip &> /dev/null; then
    ip addr show
elif command -v ifconfig &> /dev/null; then
    ifconfig
else
    echo "Could not find 'ip' or 'ifconfig' command to show local IP."
fi

echo ""
echo "[INFO] Attempting to trace route to google.com (max 10 hops)..."
if command -v traceroute &> /dev/null; then
    traceroute -m 10 google.com
elif command -v tracert &> /dev/null; # For Windows-like environments if MinGW/Cygwin used
    tracert -h 10 google.com
else
    echo "Could not find 'traceroute' or 'tracert' command."
fi

echo ""
echo "--- Network Check Finished ---"
exit 0