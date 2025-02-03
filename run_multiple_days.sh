#!/bin/bash

# Temporarily set LC_NUMERIC to use period as decimal separator
LC_NUMERIC=C

# Define the list of days/solar exposure data sets
days_list=( $(seq 170 70 240) )

# Define config paths
docker_config="ors/docker-compose.yml"
config="config/config_sample.yaml"

# Define port number
port="8080"

# Stop the ORS container if running to rebuild with new solar exposure data
docker compose -f $docker_config stop

# Loop through days and execute script
for day in "${days_list[@]}"
do
    # Replace solar exposure data path in ors-config and config file
    sed -i "s/streets_shadow_index_.*/streets_shadow_index_$day.csv/" "$docker_config"
    sed -i "s/day:.*/day: $day/" "$config"

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
            echo "Local ORS is ready. Running the script for day $day..."
        fi
    done

    # Run the script
    python src/run.py -c $config

    # Change solar exposure data path in ors-config file back to default
    sed -i "s/streets_shadow_index_.*/streets_shadow_index_170.csv/" "$docker_config"

    # Stop the ORS container to rebuild with new solar exposure data
    docker compose -f $docker_config stop
done
echo "Setting values back to default..."
sed -i "s/day:.*/day: 170/" "$config"

echo "Finished running the script for all days."
