#!/bin/bash

# Check if the file path is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_file>"
    exit 1
fi

# Extract the file name without extension
fileNameWithoutExtension=$(basename "$1" .yaml)

# Split the file name using the '-' character
IFS='-' read -ra fileParts <<< "$fileNameWithoutExtension"

# Take only the first part of the file name
baseFileName=${fileParts[0]}

# Construct the path for the sealed-secret file
sealedSecretFilePath=$(dirname "$1")/"$baseFileName-sealed-secret.yaml"

# Execute the kubeseal command
kubeseal -f "$1" -w "$sealedSecretFilePath" --controller-namespace sealed-secrets --controller-name sealed-secrets

echo "Sealed secret file created at $sealedSecretFilePath"
