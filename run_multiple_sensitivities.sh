#!/bin/bash

# Temporarily set LC_NUMERIC to use period as decimal separator
LC_NUMERIC=C

# Define the list of sensitivity factors
sensitivities_list=( $(seq 0.2 0.2 1.0) )

# Define config path
docker_config="ors/docker-compose.yml"
config="config/config_test.yaml"

# Define port number
port="8080"

# Stop the ORS container if running to rebuild with new solar exposure data
docker compose -f $docker_config stop

# (Re-)build docker container
docker compose -f $docker_config up -d

# Check ORS health status and continue when ready
echo "Waiting for local ORS..."
health_status=""
until [ "$health_status" == "ready" ]
do
    # Check ORS health status
    health_status=$(curl -s http://localhost:$port/ors/v2/health | jq -r '.status')

    if [ "$health_status" == "ready" ]; then
        echo "Local ORS is ready."
    fi
done

# Loop through days and execute script
for sensitivity in "${sensitivities_list[@]}"
do
    echo "Running for sensitivity factor $sensitivity..."
    # Replace sensitivity factor in the config file
    sed -i "s/sensitivity_factor:.*/sensitivity_factor: $sensitivity/" "$config"

    # Run the script
    python src/run.py -c $config

done

# Stop the ORS container
docker compose -f $docker_config stop

echo "Setting values back to default..."
sed -i "s/sensitivity_factor:.*/sensitivity_factor: 1.0/" "$config"

echo "Finished running the script for all sensitivities."
