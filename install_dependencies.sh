#!/bin/bash

# Download get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# Install pip using Python3
python3 get-pip.py

# Install required packages
python3 -m pip install openai beautifulsoup4 routingpy "urllib3<2.0.0"

# Clean up
rm get-pip.py

echo "Installation complete!"
