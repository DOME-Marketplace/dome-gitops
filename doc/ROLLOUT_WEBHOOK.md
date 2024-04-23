# Integration of Rollout Injecting Webhook

The following documentation describes the steps needed to add [Rollout Injecting Webhook](https://github.com/wistefan/rollout-injecting-webhook) at the cluster level. It also explains how to configure it in order to make it inject rollouts on a specific namespace. Further information on Rollout Injecting Webhook can be found [here](https://github.com/wistefan/rollout-injecting-webhook/blob/main/README.md).



## Configure Rollout Injecting Webhook on the cluster

The following steps have to be done only at the first cluster configuration, in order to make the webhook work on its first namespace. Other namespaces can be added using the instructions given in the following paragraph.

1. At cluster level, create a cluster role as specified [here](/applications_dev/rollout_webhook_test/rollout-webhook/cluster-role.yaml);
2. At desired namespace level, create a service account named rollout-webhook, as specified [here](/applications_dev/rollout_webhook_test/rollout-webhook/service-account.yaml). Service account will be used by the webhook to inject the rollouts in the namespace, so it has to be named exactly rollout-webhook in order to be found by the webhook service;
3. At cluster level, create a role binding for the service account and the cluster role, as specified [here](/applications_dev/rollout_webhook_test/rollout-webhook/role-binding.yaml);
4. At cluster level, create a certificate to be used by the webhook. This could be a self-signed(see [issuer](/applications_dev/rollout_webhook_test/rollout-webhook/self-signed-issuer.yaml) and [certificate](/applications_dev/rollout_webhook_test/rollout-webhook/certificate.yml)) certificate, issued by [cert-manager](https://cert-manager.io/);
5. Deploy the webhook server: it has to be deployed at namespace level. The specific namespace is not important: you can use the namespace you prefer, including the default. Maybe the best way is to create a specific namespace for this deployment ( eg. argo-rollout-injecting-webhook ). See [deployment](/applications_dev/rollout_webhook_test/rollout-webhook/deployment.yaml) for a sample server deployment: you'll need to set deployment and service correct namespace and check certificate configuration;
6. At cluster level, create the webhook configuration. A sample configuration can be found [here](/applications_dev/rollout_webhook_test/rollout-webhook/mutating-webhook.yaml). You'll need to configure the namespace on which you want to inject rollouts changing the `values`attribute in `namespaceSelector` stanza. Also check annotations if you used [cert-manager](https://cert-manager.io/) to create the certificate;

If everything goes fine, you should find webhook server pod deployed on the namespace you choose. You can check logs of the server using the following command:

```sh
kubectl logs -f <POD NAME> --namespace <WEBHOOK SERVER NAMESPACE>
```

Now you can start adding your deployments to the selected namespace: they will be scaled to 0 and the related rollouts will be created using the deployments as templates. A preview service will also be created starting with the original service used for the deployment. At the end of the process you'll have a BlueGreen strategy rollout created automatically for each deployment in the configured namespace.

In order to exclude a deployment from being replaced by a rollout in the configured namespace, just add the annotation:

```
metadata:
  name: webhook-server
  annotations:
    wistefan/rollout-injecting-webhook: ignore
```



## Adding namespaces to rollout webhook configuration

Once the rollout injecting webhook has been configured on the cluster, you can add more different namespaces to those handled by the webhook. Just follow these steps:

1. At desired namespace level, create a service account named rollout-webhook, as specified [here](/applications_dev/rollout_webhook_test/rollout-webhook/service-account.yaml). Service account will be used by the webhook to inject the rollouts in the namespace, so it has to be named exactly rollout-webhook in order to be found by the webhook service;
2. At cluster level, create a role binding for the service account and the cluster role, as specified [here](/applications_dev/rollout_webhook_test/rollout-webhook/role-binding.yaml);
3. Modify and apply the webhook configuration in order to add the desired namespace: you'll need to add it to the`values`attribute in `namespaceSelector` stanza;

