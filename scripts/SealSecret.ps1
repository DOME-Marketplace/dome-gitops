param(
    [string]$secretPath
)

# Check if the file path is provided
if (-not $secretPath) {
    Write-Host "Usage: ./SealSecret.ps1 -secretPath <path_to_file>"
    exit 1
}

# Extract the file name without extension
$fileNameWithoutExtension = [System.IO.Path]::GetFileNameWithoutExtension($secretPath)

# Split the file name using the '-' character
$fileParts = $fileNameWithoutExtension -split '-'

# Take only the first part of the file name
$baseFileName = $fileParts[0]

# Construct the path for the sealed-secret file
$sealedSecretFilePath = [System.IO.Path]::Combine((Get-Item $secretPath).Directory.FullName, "$baseFileName-sealed-secret.yaml")

# Execute the kubeseal command
$kubesealCommand = "kubeseal -f $secretPath -w $sealedSecretFilePath --controller-namespace sealed-secrets --controller-name sealed-secrets"
Invoke-Expression -Command $kubesealCommand

Write-Host "Sealed secret file created at $sealedSecretFilePath"
