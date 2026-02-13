#!/bin/bash
set -e

# ==============================================================================
# SCRIPT: generate_kubeconfig.sh
# DESCRIPTION: Generates a namespace-scoped kubeconfig file for a specific user.
#              It creates the Namespace, ServiceAccount, Role, RoleBinding, and Secret.
#              It automatically detects the Kubernetes API Server URL from the current context.
#
# USAGE: ./generate_kubeconfig.sh <template_path> <output_path> <namespace> <env_suffix>
# EXAMPLE: ./generate_kubeconfig.sh ./templates ./accounts marketplace prod
# ==============================================================================

# --- 1. Argument Validation ---
if [ "$#" -ne 4 ]; then
    echo "Error: Invalid number of arguments."
    echo "Usage: $0 <template_path> <output_path> <namespace> <env_suffix>"
    echo "Example: $0 ./templates ./accounts marketplace prod"
    exit 1
fi

TEMPLATE_PATH=$1
OUTPUT_PATH=$2
NAMESPACE=$3
ENV_SUFFIX=$4

# --- 2. Auto-detect Server URL ---
echo "INFO: Detecting Kubernetes API Server URL from current context..."
# Retrieves the server URL of the currently active kubectl context
SERVER_URL=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')

if [ -z "$SERVER_URL" ]; then
    echo "ERROR: Could not detect Server URL. Ensure kubectl is configured and a context is active."
    exit 1
fi
echo "INFO: Server URL detected: $SERVER_URL"

# --- 3. Prepare Output Directory ---
# The target directory will be: output_path/namespace
TARGET_DIR="$OUTPUT_PATH/$NAMESPACE"
mkdir -p "$TARGET_DIR"

echo "----------------------------------------------------"
echo "STARTING GENERATION FOR NAMESPACE: $NAMESPACE ($ENV_SUFFIX)"
echo "----------------------------------------------------"

# --- 4. Process Manifest Templates ---
# Loop through all .yaml files in the templates directory (excluding subdirectories like 'config')
echo "INFO: Processing manifest templates..."

for file in "$TEMPLATE_PATH"/*.yaml; do
    # Skip if no yaml files found or if it's a directory
    [ -e "$file" ] || continue
    
    filename=$(basename "$file")
    content=$(<"$file")
    
    # Replace placeholders
    # %NAMESPACE% -> The target namespace
    # %ENV%       -> The environment suffix (e.g., prod, dev)
    content="${content//%NAMESPACE%/$NAMESPACE}"
    content="${content//%ENV%/$ENV_SUFFIX}"
    
    # Write processed file to target directory
    echo "$content" > "$TARGET_DIR/$filename"
done

echo "INFO: Manifests generated in: $TARGET_DIR"

# --- 5. Apply Manifests to Cluster ---
echo "INFO: Applying manifests to Kubernetes cluster..."
# Apply all files in the target directory
kubectl apply -f "$TARGET_DIR/"

# --- 6. Wait for ServiceAccount Token Secret ---
# Since Kubernetes 1.24+, we manually create a Secret. We must wait for the Token Controller to populate it.
SECRET_NAME="$NAMESPACE-sa-token-$ENV_SUFFIX"
echo "INFO: Waiting for Secret '$SECRET_NAME' to be populated..."

found=0
# Retry loop (max 10 seconds)
for i in {1..10}; do
    if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" > /dev/null 2>&1; then
        found=1
        break
    fi
    sleep 1
done

if [ $found -eq 0 ]; then
    echo "ERROR: Timeout waiting for secret '$SECRET_NAME'. Please check if the ServiceAccount was created correctly."
    exit 1
fi

# --- 7. Extract Credentials ---
echo "INFO: Extracting CA Certificate and Token..."

# Extract CA Certificate (already base64 encoded in the secret)
CA_CRT=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data.ca\.crt}')

# Extract Token (base64 encoded in secret), then decode it for the kubeconfig
TOKEN_B64=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data.token}')
# Decode base64 (Linux/MacOS compatible attempt)
TOKEN=$(echo "$TOKEN_B64" | base64 --decode 2>/dev/null || echo "$TOKEN_B64" | base64 -D)

# --- 8. Generate Final Kubeconfig ---
KUBE_TEMPLATE="$TEMPLATE_PATH/config/kube-config-template.yaml"

if [ ! -f "$KUBE_TEMPLATE" ]; then
    echo "ERROR: Kubeconfig template not found at $KUBE_TEMPLATE"
    exit 1
fi

echo "INFO: Building kubeconfig file..."
config_content=$(<"$KUBE_TEMPLATE")

# Replace all placeholders in the kubeconfig template
config_content="${config_content//%NAMESPACE%/$NAMESPACE}"
config_content="${config_content//%CA_CRT%/$CA_CRT}"
config_content="${config_content//%TOKEN%/$TOKEN}"
config_content="${config_content//%SERVER_URL%/$SERVER_URL}"
config_content="${config_content//%ENV%/$ENV_SUFFIX}"
# Define a user name for the config file context
config_content="${config_content//%USER%/$NAMESPACE-user-$ENV_SUFFIX}"

# Write the final file
FINAL_FILENAME="kubeconfig-$NAMESPACE-$ENV_SUFFIX.yaml"
FINAL_FILE_PATH="$TARGET_DIR/$FINAL_FILENAME"
echo "$config_content" > "$FINAL_FILE_PATH"

echo "----------------------------------------------------"
echo "SUCCESS!"
echo "Kubeconfig generated at: $FINAL_FILE_PATH"
echo "----------------------------------------------------"