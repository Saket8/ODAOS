# Task 2.3: OCI Infrastructure Setup

## Objective
Configure OCI infrastructure for production ODAOS deployment including VCN peering, OKE cluster, and OCI services.

## Prerequisites
- Task 2.2 completed (Kubernetes Manifests)
- OCI CLI configured with CTSISGCMTPAAS profile
- Terraform installed (optional but recommended)

## Tasks

### 2.3.1 Setup VCN Peering
- [ ] Identify existing Database VCN
- [ ] Create new OKE VCN (if needed)
- [ ] Create Local Peering Gateway in DB VCN
- [ ] Create Local Peering Gateway in OKE VCN
- [ ] Establish peering connection
- [ ] Update route tables for peering traffic
- [ ] Update security lists to allow traffic

### 2.3.2 Create OKE Cluster
- [ ] Create OKE cluster via OCI Console or Terraform
  - [ ] Cluster Type: Enhanced
  - [ ] Kubernetes Version: Latest stable (1.28+)
  - [ ] VCN-Native CNI for performance
- [ ] Create Node Pool
  - [ ] Shape: VM.Standard.E4.Flex
  - [ ] OCPUs: 2 per node
  - [ ] Memory: 16GB per node
  - [ ] Node count: 3 (across ADs)
  - [ ] Boot volume: 100GB

### 2.3.3 Configure OKE Access
- [ ] Download kubeconfig file
- [ ] Test cluster access: `kubectl get nodes`
- [ ] Install OCI CSI driver for block storage
- [ ] Install Metrics Server for HPA

### 2.3.4 Setup OCI Container Registry (OCIR)
- [ ] Create repository for ODAOS images
- [ ] Configure authentication token
- [ ] Push images to OCIR
- [ ] Verify images accessible from OKE

### 2.3.5 Setup OCI Vault
- [ ] Create Vault in compartment
- [ ] Create secrets:
  - [ ] ORACLE_PASSWORD
  - [ ] GROQ_API_KEY
  - [ ] OCI_PRIVATE_KEY
- [ ] Configure RBAC for secret access
- [ ] Update code to retrieve secrets from Vault

### 2.3.6 Setup OCI Object Storage
- [ ] Create bucket for logs (`odaos-logs`)
- [ ] Create bucket for ML models (`odaos-models`)
- [ ] Configure lifecycle policies
- [ ] Enable versioning for models bucket

### 2.3.7 Setup OCI Logging & Monitoring
- [ ] Enable OCI Logging for OKE pods
- [ ] Create custom metrics in OCI Monitoring
- [ ] Create alarms for critical metrics:
  - [ ] High CPU utilization
  - [ ] High memory usage
  - [ ] Pod restart count
  - [ ] Error rate threshold

## Completion Criteria
- [ ] VCN peering established and verified
- [ ] OKE cluster running with 3 nodes
- [ ] kubeconfig working from laptop
- [ ] Images pushed to OCIR
- [ ] Vault secrets created
- [ ] Object Storage buckets created
- [ ] Monitoring alarms configured

## Estimated Duration
**6-8 hours**

## OCI Architecture
```
┌─────────────────────────────────────────┐
│  OKE VCN (10.0.0.0/16)                 │
│  ├── OKE Cluster (3 nodes)             │
│  └── Local Peering Gateway             │
└──────────────┬──────────────────────────┘
               │ VCN Peering
┌──────────────▼──────────────────────────┐
│  Database VCN (192.168.0.0/16)         │
│  └── OCI Base VM Database              │
└─────────────────────────────────────────┘

Supporting Services:
├── OCI Vault (secrets)
├── OCI Object Storage (logs, models)
├── OCI Container Registry (images)
├── OCI Logging (pod logs)
└── OCI Monitoring (metrics, alarms)
```

## Dependencies
- Task 2.2 (Kubernetes Manifests)

## Phase 1 Reuse
- OCI credentials already configured
- Database already provisioned
- CTSISGCMTPAAS profile works in production
