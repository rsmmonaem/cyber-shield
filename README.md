# Cyber-Shield (Per-Domain Resource Isolation & Protection Platform)

A Production-Grade Multi-Tenant Isolation, Request Protection, and SRE Observability Platform for **AlmaLinux 9**, **CyberPanel**, **OpenLiteSpeed (OLS)**, **LSAPI / lsphp**, **Laravel**, **Redis**, **MariaDB/PostgreSQL**, and **Docker**.

---

## 🚀 One-Click Installation

To install **Cyber-Shield** on any AlmaLinux 9 CyberPanel server, run the following command as `root`:

```bash
curl -sL https://raw.githubusercontent.com/rsmmonaem/cyber-shield/main/install.sh | bash
```

The installer will automatically:
1. Create pre-flight safety backups of OpenLiteSpeed and CyberPanel configurations.
2. Generate Linux `cgroup v2` memory, CPU, IO, and PID isolation boundaries per domain.
3. Apply OpenLiteSpeed request protection and Cloudflare Real-IP rules.
4. Launch the `domain-guardian` automated policy engine.
5. Launch the live **SRE Admin Dashboard** on port `8088`.

---

## Directory Structure

```
cyber-shield/
├── discovery/           # System Audit & Domain Ownership Inventory
├── cgroups/             # cgroup v2 & systemd Slices Engine
├── ols_protection/      # OpenLiteSpeed Request Rate-Limiting & Cloudflare Settings
├── socket_monitor/      # TCP CLOSE-WAIT Forensic Connection Engine
├── daemon/              # Queue Worker Isolation & Degradation Policy Engine
├── dashboard/           # Live SRE Web Dashboard
├── metrics/             # SQLite Time-Series Metric Collector
├── safety/              # Backups, Rollback & Deployment Runner
├── tests/               # Failure Testing Suite & Incident Analyzer
└── docs/                # Architecture Specs & Documentation
```

---

## Manual Execution & Workflows

If you have cloned the repository manually, you can run the following operations:

### 1. Run Pre-flight Discovery
```bash
./discovery/discover_system.sh /tmp/system_discovery.json
./discovery/discover_domains.sh /tmp/domain_discovery.json
```

### 2. Deploy Platform in OBSERVE ONLY Mode (Safe Pre-flight)
```bash
./safety/deploy_platform.sh observe
```

### 3. Execute Containment Acceptance Test (Failure Injection)
```bash
./tests/failure_injector.sh testdomain.com cpu 15
```

### 4. Emergency Rollback
If you ever need to restore your server's exact original configuration, run:
```bash
./safety/rollback.sh
```

---

## Accessing the Dashboard

After installation, open your web browser and navigate to:
`http://<YOUR-SERVER-IP>:8088`

You will see real-time tracking of:
* Domain CPU, RAM, and Disk IO usage
* Active connections, FDs, and CLOSE-WAIT sockets
* Active PHP workers and live request rates
* System status warnings and cgroup throttles
