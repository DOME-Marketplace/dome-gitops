Sometimes the PODs get deployed to the node ingress-pool-xyz

That node was meant to be used by ingress controller and is not so performant as other nodes.

There is a way to make sure POD doesn't get deployed to that node. We can impact the behaviour by setting node affinity rules.
You need to define the pod so that it avoids the node with label:

    nodepool: ingress

Example can be found in file *pod_affinity_example.yaml*.

    