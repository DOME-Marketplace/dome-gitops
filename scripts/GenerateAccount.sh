#!/bin/bash

# usage:
# .\GenerateAccount.sh ./templates ../accounts <namespace> <server url>

templatePath=$1
outputPath=$2
namespace=$3
serverUrl=$4

# Replace placeholder NAMESPACE within file at filePath
replace_namespace_placeholder_in_file() {
    filePath=$1
    outputDirectory=$2

    # Read file content
    templateContent=$(<"$filePath")

    # Replace placeholder NAMESPACE with the given value
    placeholder="NAMESPACE"
    templateContent="${templateContent//\%$placeholder\%/$namespace}"

    # Create target directory if it doesn't exist
    mkdir -p "$outputDirectory"

    # Build output file path
    outputFile="$outputDirectory/$(basename "$filePath")"

    # Write content
    echo "$templateContent" > "$outputFile"
}

# Build output directory path
outputDirectory="$outputPath/$namespace"

# Retrieve the list of YAML file within template directory
templateFiles=("$templatePath"/*.yaml)

echo "Generating manifest files for namespace $namespace..."

# For each file in the template directory, apply replace function
for file in "${templateFiles[@]}"; do
    replace_namespace_placeholder_in_file "$file" "$outputDirectory"
done

echo "Manifest files generated: $outputDirectory"

echo "Applying files..."

kubectl apply -f $outputDirectory/namespace.yaml
kubectl apply -f $outputDirectory/service-account.yaml
kubectl apply -f $outputDirectory/token.yaml
kubectl apply -f $outputDirectory/role.yaml
kubectl apply -f $outputDirectory/role-binding.yaml

echo "Generating kube configs..."

# Check if the 'yq' command is installed, otherwise install it
if ! command -v yq &> /dev/null; then
    echo "'yq' command is not installed. Installing now..."

    # Check the operating system and install yq
    if [ -x "$(command -v snap)" ]; then
        sudo snap install yq
    elif [ -x "$(command -v apt-get)" ]; then
        sudo apt-get update
        sudo apt-get install yq -y
    elif [ -x "$(command -v yum)" ]; then
        sudo yum install epel-release -y
        sudo yum install yq -y
    elif [ -x "$(command -v brew)" ]; then
        brew install yq
    else
        echo "Unable to install 'yq'. Make sure to install it manually and try again."
        exit 1
    fi
fi

# Build secret name
secretName="$namespace-sa-secret"

# Execute the kubectl command to get secret details in YAML format
secretYaml=$(kubectl get secret $secretName -n $namespace -o yaml)

# Extract the values of "ca.crt" and "token" from the "data" section
caCrtBase64=$(echo "$secretYaml" | yq eval '.data."ca.crt"' -)
tokenBase64=$(echo "$secretYaml" | yq eval '.data.token' -)

# Decode the token from base64
tokenDecoded=$(echo "$tokenBase64" | base64 --decode)

templateContent=$(<"$templatePath/config/kube-config.yaml")
templateContent="${templateContent//\%NAMESPACE\%/$namespace}"
templateContent="${templateContent//\%CA_CERT\%/$caCrtBase64}"
templateContent="${templateContent//\%TOKEN\%/$tokenDecoded}"
templateContent="${templateContent//\%KUBE_SERVER_URL\%/$serverUrl}"

mkdir -p "$outputDirectory/config"

# Write content
echo "$templateContent" > "$outputDirectory/config/kube-config.yaml"

echo "Kube configs generated: $outputDirectory\config\kube-config.yaml"
