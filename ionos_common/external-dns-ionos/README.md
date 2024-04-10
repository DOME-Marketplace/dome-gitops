Setup of External DNS Ionos Webhook, according to the README.md at URL:
https://github.com/ionos-cloud/external-dns-ionos-webhook

*Prerequisite - Zone registration*
Generate token via endpoint https://api.ionos.com/auth/v1/tokens/generate;
Create Zone for the domain(s) to be used in Ionos DNS API via:

    
    curl --location --request POST 'https://dns.de-fra.ionos.com/zones' \
    --header 'Authorization: Bearer tokenValue' \
    --header 'Content-Type: application/json' \
    --data-raw '{
    "properties":{
    "description": "desc",
    "enabled": true,
    "zoneName": "example-dome-marketplace.org"
    }
    }'



Prepare SealedSecret named ionos-credentials based on the token generated via endpoint https://api.ionos.com/auth/v1/tokens/generate:
    
Secret template to be placed in file 'ionos-token-secret.yaml'

    apiVersion: v1
    data:
    token: (base-64 encoded tokenValue)
    kind: Secret
    metadata:
    creationTimestamp: null
    name: ionos-token-secret
    namespace: default

Sealed secret generation:
    

    kubeseal --format yaml < ionos-token-secret.yaml > ionos-token-sealed-secret.yaml --controller-namespace sealed-secrets  --controller-name sealed-secrets
    
    


    
