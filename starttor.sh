echo "Enabling Tor service..."
sudo systemctl enable tor

echo "Starting Tor service..."
sudo systemctl start tor

echo "Checking Tor status..."
systemctl status tor