# Task 2.5: Production Validation & Testing

## Objective
Validate production deployment with comprehensive testing.

## Prerequisites
- Task 2.4 completed (Production Deployment)
- All pods running in OKE

## Tasks

### 2.5.1 Functional Testing
- [ ] All MCP tools work from production
- [ ] Agents respond correctly to queries
- [ ] Database connectivity stable over 1 hour
- [ ] OCI cost data retrieved successfully
- [ ] Logs flowing to OCI Logging
- [ ] Metrics visible in OCI Monitoring

### 2.5.2 Performance Testing
- [ ] Response time <2 seconds for 95% of requests
- [ ] Load test: 50 concurrent users (Locust/k6)
- [ ] No memory leaks over 24 hours
- [ ] Groq API within rate limits
- [ ] HPA scales correctly under load

### 2.5.3 Security Testing
- [ ] No secrets in logs or environment variables
- [ ] TLS enabled and verified (SSL Labs A rating)
- [ ] Network policies restrict traffic
- [ ] RBAC configured correctly
- [ ] Vulnerability scan passed (Trivy)

### 2.5.4 High Availability Testing
- [ ] Kill one pod → Traffic routes to others
- [ ] Delete one node → Pods reschedule
- [ ] Simulate DB connection loss → Graceful retry
- [ ] Test during rolling update

### 2.5.5 Disaster Recovery Testing
- [ ] Backup all manifests to Git
- [ ] Export ConfigMaps: `kubectl get cm -o yaml`
- [ ] Document restore procedure
- [ ] Test restore in staging namespace

### 2.5.6 Monitoring & Alerting Validation
- [ ] Verify CPU alarm triggers correctly
- [ ] Verify memory alarm triggers correctly
- [ ] Test notification delivery (email/Slack)
- [ ] Verify log aggregation in OCI Logging

## Completion Criteria
- [ ] All functional tests pass
- [ ] Performance SLAs met
- [ ] Security scan clean
- [ ] HA failover verified
- [ ] DR procedure documented and tested
- [ ] Monitoring alerts verified

## Estimated Duration
**4-6 hours**

## Test Scenarios

| Scenario | Test | Expected Result |
|----------|------|-----------------|
| Health Check | API call to /health | 200 OK |
| Performance Query | "Analyze database performance" | Response <30s |
| Healing Query | "Check for incidents" | Incident report |
| Cost Query | "Monthly spending" | Cost breakdown |
| HA Failover | Kill pod | Auto-restart <60s |
| Load Test | 50 concurrent users | <2s response time |

## Performance Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Response Time (P50) | <1s | OCI Monitoring |
| Response Time (P95) | <2s | OCI Monitoring |
| Availability | 99.9% | Uptime monitoring |
| Error Rate | <0.1% | Log analysis |
| Throughput | 100 req/min | Load test |

## Dependencies
- Task 2.4 (Production Deployment)

## Phase 1 Reuse
- Same test scenarios from Phase 1 UAT
- Same success criteria
