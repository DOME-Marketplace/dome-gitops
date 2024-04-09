# usage:
# .\scripts\GenerateAccount.ps1 -templatePath .\scripts\templates -outputPath .\accounts -namespace <namespace> -server <cluster server url> -env <env suffix>

param (
    [string]$templatePath,
    [string]$outputPath,
    [string]$namespace,
    [string]$server,
    [string]$env = ""
)

# Replace placeholder NAMESPACE within file at filePath
function ReplaceNamespacePlaceholderInFile {
    param (
        [string]$filePath,
        [string]$outputDirectory,
        [string]$namespace
    )

    # Read file content
    $templateContent = Get-Content -Path $filePath -Raw

    # Replace placeholder NAMESPACE with the given value
    $placeholder = "NAMESPACE"
    $templateContent = $templateContent -replace [regex]::Escape("%$placeholder%"), $namespace

    # Create target directory if it doesn't exist
    if (-not (Test-Path -Path $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory -Force
    }

    # Build output file path
    $outputFile = Join-Path -Path $outputDirectory -ChildPath (Split-Path -Leaf $filePath)

    # Write content
    $templateContent | Set-Content -Path $outputFile
}

# Build output directory path
$outputDirectory = Join-Path -Path $outputPath -ChildPath $namespace

# Retrieve the list of YAML file within template directory
$templateFiles = Get-ChildItem -Path $templatePath -Filter "*.yaml" -File

Write-Host "Generating manifest files for namespace $namespace..."

# For each file in the template directory, apply replace function
foreach ($file in $templateFiles) {
    ReplaceNamespacePlaceholderInFile  -filePath $file.FullName -outputDirectory $outputDirectory -namespace $namespace
}

Write-Host "Manifest files generated: $outputDirectory"

Write-Host "Applying files..."

kubectl apply -f $outputDirectory\namespace.yaml
kubectl apply -f $outputDirectory\service-account.yaml
kubectl apply -f $outputDirectory\token.yaml
kubectl apply -f $outputDirectory\role.yaml
kubectl apply -f $outputDirectory\role-binding.yaml

# retrieve script path
$scriptPath = $MyInvocation.MyCommand.Path
# retrieve script folder path
$scriptParentDirectory = Split-Path $scriptPath -Parent
$destinationDir = "ionos_" + $env

if($env -eq "") {
    $destinationDir = "ionos"
}

Write-Host "Moving namespace file to $destinationDir\namespaces..."

Move-Item -Path $outputDirectory\namespace.yaml -Destination $scriptParentDirectory\..\$destinationDir\namespaces\$namespace.yaml -Force

Write-Host "Generating kube configs..."

# Build secret name
$secretName = $namespace  + "-sa-secret"

# Execute the kubectl command to get secret details in YAML format
$secretYaml = kubectl get secret $secretName -n $namespace -o yaml

# Check if powershell-yaml module is installed, otherwise install it
if (-not (Get-Module -ListAvailable -Name powershell-yaml)) {
    # Install powershell-yaml
    Install-Module -Name powershell-yaml -Force -Scope CurrentUser
}

Import-Module powershell-yaml

# Convert to YAML
$secretData = $secretYaml | ConvertFrom-Yaml

# Extract the values of "ca.crt" and "token" from the "data" section
$caCrtBase64 = $secretData.data.'ca.crt'
$tokenBase64 = $secretData.data.token

# Decode the token from base64
$tokenDecoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($tokenBase64))

$templateContent = Get-Content -Path $templatePath\config\kube-config.yaml -Raw
$templateContent = $templateContent -replace [regex]::Escape("%NAMESPACE%"), $namespace
$templateContent = $templateContent -replace [regex]::Escape("%CA_CERT%"), $caCrtBase64
$templateContent = $templateContent -replace [regex]::Escape("%TOKEN%"), $tokenDecoded
$templateContent = $templateContent -replace [regex]::Escape("%KUBE_SERVER_URL%"), $server

if (-not (Test-Path -Path $outputDirectory\config)) {
    New-Item -ItemType Directory -Path $outputDirectory\config -Force
}

# Write content
$templateContent | Set-Content -Path $outputDirectory\config\kube-config.yaml

Write-Host "Kube configs generated: $outputDirectory\config\kube-config.yaml"



