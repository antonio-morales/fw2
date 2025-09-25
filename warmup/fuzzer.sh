#!/bin/bash

# Configurable variables
ENDPOINT="http://localhost:3000/api/data"  # Change to your endpoint
INTERVAL=5                                     # Seconds between sends
MIN=1                                          # Minimum random value
MAX=100                                        # Maximum random value

# Function to generate random integer between MIN and MAX
generate_random_int() {
  echo $(( RANDOM % (MAX - MIN + 1) + MIN ))
}

# Main loop: Generate and send data forever
while true; do
  RANDOM_INT=$(generate_random_int)

  # Optional: JSON body, adjust as needed
  JSON_PAYLOAD=$(jq -n --arg value "$RANDOM_INT" '{value: ($value | tonumber)}')

  echo "Sending: $JSON_PAYLOAD"

  # Send to HTTP endpoint (POST)
  curl -X POST -H "Content-Type: application/json" -d "$JSON_PAYLOAD" "$ENDPOINT"

  echo ""  # Newline for readability
  sleep $INTERVAL
done

