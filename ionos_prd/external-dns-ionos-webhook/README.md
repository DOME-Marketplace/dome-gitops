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
    "zoneName": "example-dome-marketplace-prd.org"
    }
    }'

1. Add bitnami helm chart:


    helm repo add bitnami https://charts.bitnami.com/bitnami

2. Prepare Secret / SealedSecret named ionos-credentials based on the token generated via endpoint https://api.ionos.com/auth/v1/tokens/generate:
    
    
    kubectl create secret generic ionos-credentials --from-literal=api-key=':tokenName'
kubectl create secret generic ionos-credentials --from-literal=api-key='eyJ0eXAiOiJKV1QiLCJraWQiOiJkNTA3NTQ1Ni02MmI0LTQ5NzItODk3My0zZTMyMjQ3NmU5YzEiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJpb25vc2Nsb3VkIiwiaWF0IjoxNzA5NjQ5MjU0LCJjbGllbnQiOiJVU0VSIiwiaWRlbnRpdHkiOnsicm9sZSI6ImFkbWluIiwicmVnRG9tYWluIjoiaW9ub3MuZGUiLCJyZXNlbGxlcklkIjoxLCJ1dWlkIjoiZjMzZWQ0YmMtMWZkYi00ZWNjLWI2YmItYzBhMGQ5ZDA1NThlIiwicHJpdmlsZWdlcyI6WyJEQVRBX0NFTlRFUl9DUkVBVEUiLCJTTkFQU0hPVF9DUkVBVEUiLCJJUF9CTE9DS19SRVNFUlZFIiwiTUFOQUdFX0RBVEFQTEFURk9STSIsIkFDQ0VTU19BQ1RJVklUWV9MT0ciLCJQQ0NfQ1JFQVRFIiwiQUNDRVNTX1MzX09CSkVDVF9TVE9SQUdFIiwiQkFDS1VQX1VOSVRfQ1JFQVRFIiwiQ1JFQVRFX0lOVEVSTkVUX0FDQ0VTUyIsIks4U19DTFVTVEVSX0NSRUFURSIsIkZMT1dfTE9HX0NSRUFURSIsIkFDQ0VTU19BTkRfTUFOQUdFX01PTklUT1JJTkciLCJBQ0NFU1NfQU5EX01BTkFHRV9DRVJUSUZJQ0FURVMiLCJBQ0NFU1NfQU5EX01BTkFHRV9MT0dHSU5HIiwiTUFOQUdFX0RCQUFTIiwiQUNDRVNTX0FORF9NQU5BR0VfRE5TIiwiTUFOQUdFX1JFR0lTVFJZIl0sImlzUGFyZW50IjpmYWxzZSwiY29udHJhY3ROdW1iZXIiOjMxOTcwNDI3fSwiZXhwIjoxNzQxMjA2ODU0fQ.FShYSjJqsuqclRtdkZQqqsjDGs3OKfkkWj4tI1Fwyz5pboHR583yAd2o0lBc3KHnnroJrnJB1oiTey0HUG7TwL5NMEt8JVDnlQt3BH_7pkwsMRe4HJ3Ryhf-hYl2-mQBYYPcS3dDrYCv77pF6mgl9Ov8z5R_FHh_dyF5UqPG91kuVYuRTCIk6U1I9VWlsNv26OXDKge7dcL6HnhZ7hddktcg7H7AYaBNL5Gd5qxH-VzHwlko-Jv0OMNc7NI4nzqoOX6Ca3T66XCU39nuGuHrLs9m5Z-cI3b6JIEX_RowTicUZw1WUgWqpyfRZmsLdqNJYfqR0Apd-x9tDLuO6VNLRg'

3. Install helm chart
    
    
    helm install external-dns-ionos bitnami/external-dns -f values.yaml

4. Test:


    kubectl --namespace=default get pods -l "app.kubernetes.io/name=external-dns,app.kubernetes.io/instance=external-dns-ionos"

5. Test - Deploy an echo server application by using the file echoserver_app.yaml. 

Preconditions - to do in mein.ionos.de system: 
- Register subdomain 'test'
- Link IP of Ingress Controller with the domain dome-marketplace-prd.org
    
    
    kubectl create ns echoserver
    kubectl apply -f test-external-dns/echoserver_app_prd.yaml
    curl http://test.dome-marketplace-prd.org/
    curl -I test.dome-marketplace-prd.org/?echo_code=404-300

