Custom Storage Protocol Benchmarking Tool

This project implements a prototype for a high-performance custom storage protocol, using fio as the load generation engine.

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
