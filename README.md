# Custom Storage Protocol Benchmarking Tool

This project implements a prototype for a high-performance custom storage protocol, using `fio` as the load generation engine. The included Python harness automates the execution of multiple performance profiles (OLTP, Streaming, Baseline, and Network).

## 🛠 Prerequisites
Ensure you have the following installed on your system:
* `git`, `gcc`, `make`, `fio`, `python3` and `iperf3`

## ⚙️ Setup & Compilation

The Makefile handles fetching dependencies, configuring FIO, and compiling the custom engine.

1. **Tune macOS Shared Memory (Required for high iodepth):**
   ```bash
   make tune-mac
   ```

   *(Note: This executes `sysctl` commands and will prompt for sudo password).*

2. **Build the Engine:**
   ```bash
   make
   ```
   *(This automatically clones the FIO repository, builds it, and compiles `the_best_protocol_ever.dylib`).*

## 🚀 Running the Benchmarks

1. **Start the Network Listener:**
   Open a separate terminal and start the `iperf3` server:
   ```bash
   iperf3 -s
   ```

2. **Execute the Test Harness:**
   Back in your main terminal, run:
   ```bash
   make run
   ```