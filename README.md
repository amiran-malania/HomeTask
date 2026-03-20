Custom Storage Protocol Benchmarking Harness
This project implements a prototype for a high-performance custom storage protocol, using fio as the load generation engine and Python for automated analytical reporting.
🛠 Prerequisites
1. FIO Source Code
To build an external ioengine, you need the fio header files.
bash
git clone https://github.com
cd fio && ./configure && make -j$(nproc)
cd ..

2. macOS System Tuning (Shared Memory)
FIO requires sufficient shared memory segments to manage async I/O buffers. The default macOS limits are often too low for high iodepth tests.
Run these commands to adjust kernel parameters:
bash
sudo sysctl -w kern.sysv.shmmax=52428800
sudo sysctl -w kern.sysv.shmall=12800
sudo sysctl -w kern.sysv.shmmni=128
sudo sysctl -w kern.sysv.shmseg=32

🏗 Compilation
Compile the custom protocol engine into a dynamic library. We use -undefined dynamic_lookup to allow the engine to hook into FIO's internal symbols at runtime.
bash
gcc -shared -fPIC -rdynamic -o the_best_protocol_ever.so \
    the_best_protocol_ever.c \
    -I./fio \
    -undefined dynamic_lookup

🚀 Running the Benchmarks
The Python harness automates the execution of multiple profiles (OLTP, Streaming, Baseline, and Network).
1. Start iperf3 Server
In a separate terminal, start the network listener:
bash
iperf3 -s

2. Execute Harness
Ensure your config.json points to the correct path of your compiled .so or .dylib.
bash
python3 benchmark_harness.py

📊 Analytical Theory
Tail Latency (P99 vs Average)
If Average Latency is low but P99 is extremely high, the system is experiencing Jitter. This is typically caused by:
Resource Contention: Locking issues or CPU spikes.
Head-of-Line Blocking: One slow request holding up the queue in the custom protocol.
Background Tasks: SSD garbage collection or system interrupts.
Network Bottlenecks
To determine if the network is the primary bottleneck, we monitor:
Retransmits: High counts indicate packet loss and link instability.
CWND (Congestion Window): Frequent collapses show the network cannot sustain the throughput.
Bandwidth Gap: If iperf3 bandwidth is significantly lower than fio storage throughput, the network is the physical limit.
Long-term Soak Testing
For 24-hour tests, we utilize fio logging flags:
--log_avg_msec: Dumps periodic performance samples to CSV.
Aggregation: Use a rolling window average to track performance degradation as the system reaches "Steady State."
