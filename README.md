# Per-Domain Resource Isolation & Request Protection Platform

A Production-Grade Multi-Tenant Isolation, Request Protection, and SRE Observability Platform for **AlmaLinux 9**, **CyberPanel**, **OpenLiteSpeed (OLS)**, **LSAPI / lsphp**, **Laravel**, **Redis**, **MariaDB/PostgreSQL**, and **Docker**.

---

## Directory Structure

```
domain-isolation-platform/
├── discovery/           # Phase 1 & 2: System Audit & Full Domain Mapping
│   ├── discover_system.sh
│   └── discover_domains.sh
├── cgroups/             # Phase 3-9: systemd Slices & cgroup v2 Engine
│   ├── package_profiles.json
│   ├── slice_generator.py
│   └── domain_cgroup_manager.py
├── ols_protection/      # Phase 10-12: Request Rate-Limiting & Cloudflare Real-IP Protection
│   └── ols_rule_generator.py
├── socket_monitor/      # Phase 13: CLOSE-WAIT & Connection Accumulation Engine
│   └── closewait_detector.py
├── daemon/              # Phase 14-20: Queue Worker Isolation & Automatic Policy Engine
│   ├── queue_isolation.sh
│   ├── db_redis_monitor.py
│   └── domain_guardian.py
├── dashboard/           # Phase 21-23: Time-Series Metrics & SRE Web Dashboard
│   ├── app.py
│   ├── alert_engine.py
│   └── static/index.html
├── metrics/             # Phase 23: Time-Series Database Collector
│   └── metrics_collector.py
├── safety/              # Phase 24-25: Backups, Rollback & 4-Stage Deployment Runner
│   ├── backup_manager.sh
│   ├── rollback.sh
│   └── deploy_platform.sh
├── tests/               # Phase 26-27: Failure Testing Suite & Incident Analyzer
│   ├── failure_injector.sh
│   └── incident_analyzer.sh
└── docs/                # Architecture Specs & Documentation
    └── ARCHITECTURE.md
```

---

## Quick Start & Operator Workflows

### 1. Run Pre-flight Discovery
```bash
./discovery/discover_system.sh /tmp/system_discovery.json
./discovery/discover_domains.sh /tmp/domain_discovery.json
```

### 2. Deploy Platform in OBSERVE ONLY Mode (Safe Pre-flight)
```bash
./safety/deploy_platform.sh observe
```

### 3. Launch Live SRE Admin Dashboard
```bash
python3 dashboard/app.py
```
Open browser at `http://<SERVER-IP>:8088`.

### 4. Execute Containment Acceptance Test
```bash
./tests/failure_injector.sh testdomain.com cpu 15
```

### 5. Emergency Rollback
```bash
./safety/rollback.sh
```
