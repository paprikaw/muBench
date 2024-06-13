# µBench Docker Image

This image contains 

- µBench software of this folder
- kubectl
- istioctl
- helm
- Apache ab tools for benchmarking
- vim, nano, iproute2, iputils-ping

To build you could use 

```zsh
docker build -t xu/mubench .
```

Copy `.kube/config` into `/root/.kube/config` container folder to access Kubernetes cluster from the container. In case update the `server:` key with the correct IP address. 
Be careful to use the correct K8s dns service url in `Configs/K8sParameters.json`
