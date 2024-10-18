# External Access to TMForum

In order to access the TMForum APIs in the SBX-Environment, [Apisix](https://apisix.apache.org/) is deployed as an ApiGateway, supporting access via Api-Keys. 

## Register an API-Key

In order to keep the keys secure, a new key has to be registered via PullRequest. 

1. Register the new consumer in the [values.yaml](../ionos_sbx/marketplace/iam/apisix/values.yaml) at:

```yaml
  consumers:
    # -- name of the consumer to be created
    - name: ficodes
      # -- env var that provides the API Key, needs to match the extraEnvVarsSecret containing the actual key
      varName: FICODES_API_KEY 
    - name: <NEW_CONSUMER>
      varName: <NEW_CONSUMER>_API_KEY
```

<NEW_CONSUMER> needs to be replaced with the unique name of the new api-consumer. The name is only allowed to contain normal characters, no special characters at all.
<NEW_CONSUMER>_API_KEY is the name of the environment variable that will contain the key. 

2. Create a secret containing the ApiKey:

    1. Create the secret:
    ```yaml
        apiVersion: v1
        kind: Secret
        metadata:
            name: <NEW_CONSUMER>-apikey-secret
            namespace: marketplace
        type: Opaque
        data:
            API_KEY: <BASE_64_ENCODED_KEY>
    ```
    2. The <BASE_64_ENCODED_KEY> should contain the sufficently long api-key. It needs to be base64-encoded.

    3. Seal the secret following the standard workflow described here: [Add secrets](./INTEGRATION.md/#add-secrets)

    4. Add the sealed-secret to the [apisix-templates folder](../ionos_sbx/marketplace/iam/apisix/templates/)

3. Register the environment variable in the [values.yaml](../ionos_sbx/marketplace/iam/apisix/values.yaml) at:

```yaml
    extraEnvVars:
      # -- env var read from the secret
      - name: FICODES_API_KEY
        valueFrom:
          secretKeyRef:
            name: ficodes-env-secret
            key: API_KEY
      - name: <NEW_CONSUMER>_API_KEY
        valueFrom:
          secretKeyRef:
            name: <NEW_CONSUMER>-apikey-secret
            key: API_KEY
```

Make sure that <NEW_CONSUMER>_API_KEY and <NEW_CONSUMER>-apikey-secret exactly match the values you used in the previous steps.

4. Commit, push and create a PR

Once the PR is merged, the api-key can be used.

## Access the TMForum APIs

The APIs can be accessed as sub-paths of ```tmforum.dome-marketplace-sbx.org```. See [the routes configuration](../ionos_sbx/marketplace/iam/apisix/values.yaml#l61) for all available APIs. Currently, only GET requests are allowed when a valid ApiKey is provided.

The following example will return the list of registered catalogs:
```bash
    curl -X GET "https://tmforum.dome-marketplace-sbx.org/product-catalog/catalog \
        -H 'accept: application/json;charset=utf-8' \
        --header "api-key: <YOUR_REGISTERD_KEY>"
```