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

1. Add bitnami helm chart:


    helm repo add bitnami https://charts.bitnami.com/bitnami

2. Prepare Secret / SealedSecret named ionos-credentials based on the token generated via endpoint https://api.ionos.com/auth/v1/tokens/generate:
    
    
    kubectl create secret generic ionos-credentials --from-literal=api-key=':tokenName'

3. Install helm chart
    
    
    helm install external-dns-ionos bitnami/external-dns -f /values.yaml

4. Test:


    kubectl --namespace=default get pods -l "app.kubernetes.io/name=external-dns,app.kubernetes.io/instance=external-dns-ionos"

5. Test - Deploy an echo server application by using the file echoserver_app.yaml. 
    

    kubectl create ns echoserver
    kubectl apply -f echoserver_app.yaml
    curl -I tmforum-doc.dome-marketplace-sbx.org/?echo_code=404-300
    
6. Check DNS Records (for some reason now it's returning empty list)

    
    curl --location --request GET 'https://dns.de-fra.ionos.com/records?filter.name=app' \
    --header 'Authorization: Bearer token' \
    --data ''
