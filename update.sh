#!/bin/bash

# Get the current timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")

# Define the source and backup file names
source_file="app.py"
backup_file="app.py.$timestamp"

# Check if the source file exists
if [ ! -f "$source_file" ]; then
    echo "Error: $source_file does not exist."
    exit 1
fi

# Create the backup
cp "$source_file" "$backup_file"

# Check if the backup was successful
if [ $? -eq 0 ]; then
    echo "Backup created successfully: $backup_file"
else
    echo "Error: Failed to create backup."
    exit 1
fi

mv ~/Downloads/simplified-app-py.py app.py
