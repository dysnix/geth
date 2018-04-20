# Description

This is work-around for auto-restart geth if node not syncing (issues like [this](https://github.com/ethereum/go-ethereum/issues/15067))

# Requirements
* Kubernetes 1.8 or highest version
* Ethereum node (we using [helm chart](https://github.com/arilot/charts/tree/geth/incubator/geth), but you can use
any geth provision solution.
* Geth RPC Kubernetes service name *must* include `geth` in name

# Usage
* Use image `arilot/geth`
* Add liveness section

Example:

```
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: ethereum-geth
spec:
  template:
    metadata:
      labels:
        app: geth
    spec:
      containers:
      - command:
        - bash
        - -c
        - gunicorn -b 0.0.0.0 app:app --daemon && geth --syncmode fast=
        image: arilot/geth
        imagePullPolicy: Always
        livenessProbe:
          failureThreshold: 1
          httpGet:
            path: /healthz
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 300
          periodSeconds: 300
          successThreshold: 1
          timeoutSeconds: 30
        name: ethereum-geth
        ports:
        - containerPort: 8545
          name: rpc
          protocol: TCP
        - containerPort: 8546
          name: ws
          protocol: TCP
        volumeMounts:
        - mountPath: /root
          name: data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: ethereum-geth
```
