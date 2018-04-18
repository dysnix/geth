# Description

This is work-around for auto-restart geth if node not syncing (issues like [this](https://github.com/ethereum/go-ethereum/issues/15067))

# Requirements
* Kubernetes 1.8 or highest version
* Ethereum node (we using [helm chart](https://github.com/arilot/charts/tree/geth/incubator/geth), but you can use
any geth provision solution.
* Geth RPC Kubernetes service name *must* include `geth` in name

# Usage

Add this section to spec.containers section of your Geth yaml-file. Example:

      - name: liveness
        image: arilot/geth-kubernetes-checker
        livenessProbe:
          failureThreshold: 3
          httpGet:
            path: /healthz
            port: 5000
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          successThreshold: 1
          timeoutSeconds: 10
        