# Task 1.2: SSH Tunnel & Database Connection

## Objective
Establish connectivity to OCI Base VM Database via SSH tunnel through Bastion host.

## Prerequisites
- Task 1.1 completed (environment setup)
- OCI Bastion host provisioned
- OCI Base VM Database running
- SSH key for Bastion access

## Tasks

### 1.2.1 Gather Connection Details
- [ ] Get Bastion public IP address
- [ ] Get database private IP address
- [ ] Locate SSH key file (`C:\Users\2016tu\.ssh\bastion_key.pem`)
- [ ] Get Oracle database credentials (username, password, service name)

### 1.2.2 Test Manual SSH Tunnel
```powershell
# Test tunnel command
ssh -L 1521:DB_PRIVATE_IP:1521 -i bastion_key.pem opc@BASTION_PUBLIC_IP -N
```
- [ ] Verify tunnel establishes without errors
- [ ] Test localhost:1521 connectivity

### 1.2.3 Implement SSH Tunnel Manager
- [ ] Create `odaos_tools/ssh_tunnel.py`
- [ ] Implement `SSHTunnel` class with start/stop/is_active methods
- [ ] Add automatic reconnection logic
- [ ] Test tunnel manager script

### 1.2.4 Implement Oracle Connection Manager
- [ ] Create `odaos_tools/oracle_connector.py`
- [ ] Implement connection pooling (min=2, max=10)
- [ ] Add `test_connection()` method
- [ ] Add `execute_query()` method with result formatting
- [ ] Implement error handling for common Oracle errors

### 1.2.5 Validate Database Connectivity
- [ ] Test connection to database via tunnel
- [ ] Execute sample query (SELECT from v$version)
- [ ] Query tablespace usage
- [ ] Verify connection pool behavior

## Completion Criteria
- [ ] SSH tunnel establishes reliably
- [ ] Oracle connection pool created successfully
- [ ] Can execute queries and retrieve results
- [ ] Error handling works for connection failures

## Estimated Duration
**4-6 hours**

## Dependencies
- Task 1.1 (Environment Setup)
- OCI Bastion and Database provisioned

## Phase 2 Considerations
- SSH tunnel will be replaced by VCN peering in production
- Connection manager design abstracted for different connectivity modes
- Environment variable pattern works for both .env and Kubernetes secrets
