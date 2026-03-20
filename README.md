# 🚀 Custom Storage Protocol Benchmarking Harness

This project provides a **prototype benchmarking framework** for evaluating a high-performance custom storage protocol.

It combines:
- **fio** as a flexible load generator
- A **custom external ioengine**
- A **Python-based harness** for automation and analytics

The goal is to simulate real-world workloads (OLTP, streaming, etc.) and extract meaningful performance insights such as latency behavior, throughput limits, and system bottlenecks.

---

## 🧱 Architecture Overview

```
+---------------------+
| Python Harness      |
| (benchmark control) |
+----------+----------+
           |
           v
+---------------------+
| fio Load Generator  |
| (custom ioengine)   |
+----------+----------+
           |
           v
+---------------------+
| Custom Protocol     |
| (C implementation)  |
+---------------------+
```

---

## 🛠 Prerequisites

### 1. Build fio from Source

```bash
git clone https://github.com/axboe/fio
cd fio
./configure
make -j$(nproc)
cd ..
```

---

### 2. macOS System Tuning (Shared Memory)

```bash
sudo sysctl -w kern.sysv.shmmax=52428800
sudo sysctl -w kern.sysv.shmall=12800
sudo sysctl -w kern.sysv.shmmni=128
sudo sysctl -w kern.sysv.shmseg=32
```

> ⚠️ These settings are temporary and reset after reboot.

---

## 🏗 Compilation

```bash
gcc -shared -fPIC -rdynamic -o the_best_protocol_ever.so \
    the_best_protocol_ever.c \
    -I./fio \
    -undefined dynamic_lookup
```

---

## 🚀 Running Benchmarks

### 1. Start Network Baseline (iperf3)

```bash
iperf3 -s
```

### 2. Run Benchmark Harness

```bash
python3 benchmark_harness.py
```

---

## 📊 Workload Profiles

| Profile     | Description |
|------------|------------|
| Baseline   | Raw throughput |
| OLTP       | Small random I/O |
| Streaming  | Sequential I/O |
| Network    | Network limits |

---

## 📈 Analytical Model

### Tail Latency

Large gap between avg and P99 = jitter.

Causes:
- Resource contention
- Head-of-line blocking
- SSD background tasks

---

### Network Bottlenecks

Check:
- Retransmits
- CWND drops
- Bandwidth vs iperf3

---

### Soak Testing

```bash
--log_avg_msec=1000
```

---

## 📂 Project Structure

```
.
├── the_best_protocol_ever.c
├── benchmark_harness.py
├── config.json
├── results/
└── README.md
```

---

## 📜 License

MIT
