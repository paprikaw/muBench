# Prerequisite:
# 1. Install istioctl for istio installation
# Secure .kube
chmod go-r -R ~/.kube/
set -e
# Prometherus
kubectl create namespace monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Add kubernetes-dashboard repository
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
# Deploy a Helm Release named "kubernetes-dashboard" using the kubernetes-dashboard chart
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard

# Prometheus (30000) and Grafana (30001) NodePort Services
kubectl apply -f prometheus-nodeport.yaml -n monitoring
kubectl apply -f grafana-nodeport.yaml -n monitoring

# Istio
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update
kubectl create namespace istio-system
helm install istio-base istio/base -n istio-system
helm install istiod istio/istiod -n istio-system --wait
helm install istio-ingressgateway istio/gateway -n istio-system
kubectl label namespace default istio-injection=enabled

# Istio - Prometeus integration
kubectl apply -f istio-prometheus-operator.yaml

# Jarger
kubectl apply -f jaeger.yaml

# Jaeger NodePort Service (30002)
kubectl apply -f jaeger-nodeport.yaml

#Kiali
helm repo add kiali https://kiali.org/helm-charts
helm repo update
helm install \
  -n istio-system \
  -f kiali-values.yaml \
  kiali-server \
  kiali/kiali-server

#Kiali NodePort Service (30003)
kubectl apply -f kiali-nodeport.yaml
