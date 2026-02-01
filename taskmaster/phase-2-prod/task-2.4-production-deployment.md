# Task 2.4: Production Deployment

## Objective
Deploy ODAOS to OKE production environment.

## Prerequisites
- Task 2.3 completed (OCI Infrastructure)
- All Docker images pushed to OCIR
- kubectl configured for OKE cluster

## Tasks

### 2.4.1 Create Namespace & Secrets
```bash
kubectl apply -f k8s/namespace.yaml

kubectl create secret generic odaos-secrets \
  --from-literal=oracle-password=$ORACLE_PWD \
  --from-literal=groq-api-key=$GROQ_KEY \
  --from-file=oci-private-key=$OCI_KEY_FILE \
  -n odaos-prod
```

### 2.4.2 Deploy ConfigMaps & PVCs
- [ ] Apply ConfigMap: `kubectl apply -f k8s/configmap.yaml`
- [ ] Apply PVCs: `kubectl apply -f k8s/pvc-*.yaml`
- [ ] Verify PVCs bound to volumes

### 2.4.3 Deploy Applications
- [ ] Deploy MCP Servers: `kubectl apply -f k8s/deployment-mcp.yaml`
- [ ] Deploy Orchestrator: `kubectl apply -f k8s/deployment-orchestrator.yaml`
- [ ] Verify pods running: `kubectl get pods -n odaos-prod`
- [ ] Check logs for errors: `kubectl logs -f deployment/mcp-servers -n odaos-prod`

### 2.4.4 Deploy Services & Ingress
- [ ] Apply Services: `kubectl apply -f k8s/service-*.yaml`
- [ ] Apply Ingress: `kubectl apply -f k8s/ingress.yaml`
- [ ] Get Load Balancer IP
- [ ] Test health endpoints

### 2.4.5 Configure DNS
- [ ] Point domain to Load Balancer IP
- [ ] Verify TLS certificate
- [ ] Test HTTPS access

### 2.4.6 Deploy HPA
- [ ] Apply HPA: `kubectl apply -f k8s/hpa.yaml`
- [ ] Verify HPA active: `kubectl get hpa -n odaos-prod`

### 2.4.7 Validate Database Connectivity
```bash
kubectl exec -it deployment/mcp-servers -n odaos-prod -- \
  python -c "from odaos_tools.oracle_connector import OracleConnector; \
             db = OracleConnector(); db.test_connection()"
```

### 2.4.8 Test Full Workflow
- [ ] Test Performance Agent via API
- [ ] Test Self-Healing Agent via API
- [ ] Test Cost Agent via API
- [ ] Test Multi-Agent Orchestrator
- [ ] Verify response times <2 seconds

## Completion Criteria
- [ ] All pods running and healthy
- [ ] Services responding to requests
- [ ] Database connectivity verified
- [ ] Full workflows functional
- [ ] TLS working correctly
- [ ] HPA scaling verified

## Estimated Duration
**4-6 hours**

## Deployment Checklist

| Step | Command | Verification |
|------|---------|--------------|
| Namespace | `kubectl apply -f namespace.yaml` | `kubectl get ns` |
| Secrets | `kubectl create secret...` | `kubectl get secrets -n odaos-prod` |
| ConfigMap | `kubectl apply -f configmap.yaml` | `kubectl get cm -n odaos-prod` |
| PVCs | `kubectl apply -f pvc-*.yaml` | `kubectl get pvc -n odaos-prod` |
| MCP Servers | `kubectl apply -f deployment-mcp.yaml` | Pods Running |
| Orchestrator | `kubectl apply -f deployment-orchestrator.yaml` | Pods Running |
| Services | `kubectl apply -f service-*.yaml` | `kubectl get svc -n odaos-prod` |
| Ingress | `kubectl apply -f ingress.yaml` | Load Balancer IP assigned |
| HPA | `kubectl apply -f hpa.yaml` | `kubectl get hpa -n odaos-prod` |

## Dependencies
- Task 2.3 (OCI Infrastructure)

## Rollback Procedure
```bash
# If deployment fails
kubectl rollout undo deployment/mcp-servers -n odaos-prod
kubectl rollout undo deployment/agent-orchestrator -n odaos-prod
```
