# Task 2.2: Kubernetes Manifests

## Objective
Create Kubernetes manifests for deploying ODAOS to OKE.

## Prerequisites
- Task 2.1 completed (Docker Containerization)
- kubectl installed on development machine

## Tasks

### 2.2.1 Create Namespace
- [ ] Create `k8s/namespace.yaml`
- [ ] Define `odaos-prod` namespace
- [ ] Add labels for organization

### 2.2.2 Create ConfigMaps
- [ ] Create `k8s/configmap.yaml`
- [ ] Database connection settings (non-sensitive)
- [ ] OCI compartment IDs
- [ ] Groq model settings
- [ ] Log level configuration

### 2.2.3 Create Secrets Template
- [ ] Create `k8s/secret.yaml` (template only)
- [ ] Document secret creation via kubectl
- [ ] ORACLE_PASSWORD
- [ ] GROQ_API_KEY
- [ ] OCI_PRIVATE_KEY

### 2.2.4 Create Deployments
- [ ] Create `k8s/deployment-mcp.yaml`
  - [ ] 2 replicas for HA
  - [ ] Resource limits (CPU: 500m, Memory: 1Gi)
  - [ ] Liveness and readiness probes
  - [ ] Environment from ConfigMap and Secrets
- [ ] Create `k8s/deployment-orchestrator.yaml`
  - [ ] 3 replicas for HA
  - [ ] Resource limits (CPU: 1, Memory: 2Gi)
  - [ ] Probes configured

### 2.2.5 Create Services
- [ ] Create `k8s/service-mcp.yaml` (ClusterIP)
- [ ] Create `k8s/service-orchestrator.yaml` (LoadBalancer)
- [ ] Port mappings configured correctly

### 2.2.6 Create Persistent Volume Claims
- [ ] Create `k8s/pvc-logs.yaml` (10Gi)
- [ ] Create `k8s/pvc-models.yaml` (5Gi)
- [ ] Storage class: OCI Block Storage

### 2.2.7 Create HPA (Horizontal Pod Autoscaler)
- [ ] Create `k8s/hpa.yaml`
- [ ] Target CPU utilization: 70%
- [ ] Min replicas: 2, Max replicas: 10

### 2.2.8 Create Ingress
- [ ] Create `k8s/ingress.yaml`
- [ ] TLS enabled
- [ ] OCI Load Balancer integration

## Completion Criteria
- [ ] All manifest files created
- [ ] Manifests pass `kubectl apply --dry-run`
- [ ] Resource limits appropriate
- [ ] Probes configured correctly
- [ ] HA configuration complete

## Estimated Duration
**4-6 hours**

## Kubernetes Architecture
```
odaos-prod namespace
├── Deployment: mcp-servers (2 replicas)
├── Deployment: agent-orchestrator (3 replicas)
├── Service: mcp-service (ClusterIP)
├── Service: orchestrator-service (LoadBalancer)
├── ConfigMap: odaos-config
├── Secret: odaos-secrets
├── PVC: logs-pvc (10Gi)
├── PVC: models-pvc (5Gi)
├── HPA: orchestrator-hpa
└── Ingress: odaos-ingress
```

## Dependencies
- Task 2.1 (Docker Containerization)

## Phase 1 Reuse
- Configuration values from .env file
- No code changes required
