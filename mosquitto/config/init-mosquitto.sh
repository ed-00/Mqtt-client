#!/bin/bash

# Initialize Mosquitto password file for development
# This script creates a proper password file for Mosquitto

PASSWD_FILE="/mosquitto/config/password_file"
USERNAME="${MQTT_USERNAME:-user}"
PASSWORD="${MQTT_PASSWORD:-password}"

# Create password file if it doesn't exist or if environment variables are set
if [ ! -f "$PASSWD_FILE" ] || [ -n "$MQTT_USERNAME" ]; then
    echo "Creating Mosquitto password file..."
    
    # Remove existing file
    rm -f "$PASSWD_FILE"
    
    # Create new password file using mosquitto_passwd
    # This will create a properly hashed password
    echo "$PASSWORD" | mosquitto_passwd -c "$PASSWD_FILE" "$USERNAME"
    
    echo "Password file created for user: $USERNAME"
else
    echo "Password file already exists"
fi

# Set proper permissions
chmod 600 "$PASSWD_FILE"
chown mosquitto:mosquitto "$PASSWD_FILE" 2>/dev/null || true

echo "Mosquitto initialization complete" 