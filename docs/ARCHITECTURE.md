# Production Architecture Document: Per-Domain Resource Isolation & Request Protection Platform

**Platform Target Environment**: AlmaLinux 9, CyberPanel, OpenLiteSpeed (OLS), LSAPI / lsphp, Laravel / PHP applications, Redis, MariaDB / PostgreSQL, Docker, Cloudflare Proxy.

---

## 1. Primary Design Objective
The single immutable law of this platform architecture is:
> **ONE WEBSITE MUST NEVER BE ABLE TO TAKE DOWN OR SIGNIFICANTLY DEGRADE OTHER WEBSITES OR THE WHOLE SERVER.**

---

## 2. Linux cgroup v2 Slice Hierarchy

```
server.slice
    │
    └── hosting.slice
          │
          ├── package-basic.slice
          │      ├── domain-a.slice
          │      └── domain-b.slice
          │
          ├── package-business.slice
          │      ├── domain-c.slice
          │      └── domain-d.slice
          │
          └── package-enterprise.slice
                 └── domain-e.slice
```

### Domain Boundary Scope
A domain's cgroup slice (`domain-<domain>.slice`) encapsulates **all** domain-owned processes:
1. OpenLiteSpeed LSAPI worker processes (`lsphp`)
2. Laravel queue workers (`artisan queue:work`) & Horizon processes
3. Laravel scheduler & user cron processes
4. Background worker scripts & auxiliary Node/Python workers

---

## 3. Package Profiles & Resource Control

| Resource Dimension | BASIC Package | BUSINESS Package | ENTERPRISE Package |
| :--- | :--- | :--- | :--- |
| **CPU Quota / Weight** | 100% / 100 weight | 200% / 200 weight | 400% / 400 weight |
| **RAM (High / Max)** | 450M / 512M | 1.8G / 2.0G | 3.6G / 4.0G |
| **Disk I/O Bandwidth** | 10 MB/s | 30 MB/s | 100 MB/s |
| **Disk IOPS** | 1,000 IOPS | 3,000 IOPS | 10,000 IOPS |
| **Max Processes (PIDs)**| 20 processes | 50 processes | 100 processes |
| **Open Files (FDs)** | 5,000 FDs | 20,000 FDs | 50,000 FDs |
| **PHP LSAPI Workers** | 5 workers | 15 workers | 40 workers |
| **Concurrent Connections**| 100 conns | 500 conns | 2,000 conns |
| **Requests / Second** | 20 req/s | 100 req/s | 300 req/s |

---

## 4. Request Protection & Cloudflare Real-IP Configuration

1. **Cloudflare Real-IP Trusted Proxy Engine**:
   - Configures `useIpInProxyHeader 2` in OpenLiteSpeed `httpd_config.conf` with Cloudflare IPv4 & IPv6 CIDRs.
   - Prevents Cloudflare proxy IPs from being mistakenly throttled or banned.
2. **Endpoint-Specific Protection**:
   - Enforces specific rate limits on expensive routes: `/login`, `/wp-login.php`, `/xmlrpc.php`, `/api/*`, `/search`, `/checkout`, `/graphql`.
   - Returns custom HTTP 429 Too Many Requests responses when limits are exceeded.

---

## 5. CLOSE-WAIT & Connection Accumulation Engine

1. **Detection Algorithm**:
   - Periodically samples socket state table via `ss` / `/proc/net/tcp`.
   - Categorizes TCP states (`ESTABLISHED`, `CLOSE-WAIT`, `TIME-WAIT`, `SYN-RECV`).
   - Flags PIDs accumulating >50 CLOSE-WAIT sockets.
2. **Targeted Remediation**:
   - Recycles only the specific stuck LSAPI worker process (`kill -15 <pid>`).
   - **NEVER** issues global `killall litespeed` or `systemctl restart lsws`.

---

## 6. Phase 20 Graceful Degradation Order

```
[1. DETECT] → [2. LOG] → [3. WARN] → [4. SOFT THROTTLE (memory.high)] → [5. RATE LIMIT (HTTP 429)] → [6. TARGETED WORKER KILL]
```

At every tier of degradation, **all other domains on the server remain 100% isolated and unaffected**.
