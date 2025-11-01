#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HOME/.kube"
scp williamqiao@192.168.139.238:/etc/rancher/k3s/k3s.yaml "$HOME/.kube/k3s.yaml"
sed -i '' 's/127.0.0.1/192.168.139.238/' "$HOME/.kube/k3s.yaml"
