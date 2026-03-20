import subprocess
import json
import os
import socket
import sys
from multiprocessing import Process, Queue

def validate_environment(config):
    """Checks for dylib existence, symbols, and iperf3 server readiness."""
    print("--- Running Pre-flight Validation ---")
    
    # 1. Validate Custom Engine
    custom_args = config.get('custom_proto', [])
    engine_path = None
    for arg in custom_args:
        if "external:" in arg:
            engine_path = arg.split("external:")[1]
            break
    
    if engine_path:
        if not os.path.exists(engine_path):
            print(f"[ERROR] Engine not found at: {engine_path}")
            sys.exit(1)
        
        # Check for the required 'get_ioengine' symbol on macOS
        try:
            nm_output = subprocess.check_output(["nm", "-gU", engine_path], text=True)
            if "_get_ioengine" not in nm_output:
                print(f"[ERROR] {engine_path} is missing 'get_ioengine' symbol.")
                sys.exit(1)
            print(f"[OK] Custom engine validated.")
        except Exception:
            print("[SKIP] Could not run 'nm' for symbol check.")

    # 2. Validate iperf3 Server
    net_args = config.get('network', [])
    target_ip = "127.0.0.1" # default
    if "-c" in net_args:
        target_ip = net_args[net_args.index("-c") + 1]
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        try:
            s.connect((target_ip, 5201))
            print(f"[OK] iperf3 server found at {target_ip}:5201.")
        except Exception:
            print(f"[ERROR] iperf3 server not reachable at {target_ip}:5201. Run 'iperf3 -s' first.")
            sys.exit(1)
    print("--- Validation Passed ---\n")

def run_fio(name, params, queue):
    """Worker process to execute FIO with verbose error reporting."""
    # We REMOVE --quiet so we can see the initialization errors
    cmd = ["fio", "--output-format=json"] + params
    try:
        # Run without check=True so we can manually handle the result
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # This captures the REAL reason (e.g., "Permission denied" or "Invalid engine")
            error_msg = result.stderr.strip() if result.stderr else f"Exit Code {result.returncode}"
            queue.put({"name": name, "error": error_msg})
            return

        queue.put({"type": "fio", "name": name, "data": json.loads(result.stdout)})
    except Exception as e:
        queue.put({"name": name, "error": str(e)})


def run_iperf(params, queue):
    """Worker process to execute iperf3 for network baseline."""
    cmd = ["iperf3"] + params
    # Ensure --json is present
    if "--json" not in cmd: cmd.append("--json")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        queue.put({"type": "network", "name": "iperf_net", "data": json.loads(result.stdout)})
    except Exception as e:
        queue.put({"name": "iperf_net", "error": str(e)})

def aggregator(queue, count):
    """Gathers and analyzes results from all processes."""
    received = 0
    results = []
    while received < count:
        results.append(queue.get())
        received += 1

    print("\n" + "="*60 + "\nFINAL ANALYTICAL REPORT\n" + "="*60)
    for res in results:
        name = res['name']
        if "error" in res:
            print(f"[{name.upper()}] Failed: {res['error']}")
            continue
            
        if res.get("type") == "fio":
            job = res['data']['jobs'][0]
            
            # Aggregate stats (handle cases where read or write might be 0)
            r = job.get('read', {})
            w = job.get('write', {})
            
            total_bw_mib = (r.get('bw', 0) + w.get('bw', 0)) / 1024
            total_iops = r.get('iops', 0) + w.get('iops', 0)
            
            # Determine which latency source to use (read or write)
            lat_stats = r if r.get('iops', 0) > w.get('iops', 0) else w
            p99_ns = lat_stats.get('clat_ns', {}).get('percentile', {}).get('99.000000', 0)
            p99_ms = p99_ns / 1_000_000

            print(f"PROFILE: {name.upper()}")
            print(f" - Throughput: {total_bw_mib:.2f} MiB/s")
            print(f" - Total IOPS: {total_iops:.0f}")
            print(f" - P99 Latency: {p99_ms:.2f} ms\n")
            p95_ns = lat_stats.get('clat_ns', {}).get('percentile', {}).get('95.000000', 0)
            p95_ms = p95_ns / 1_000_000
            print(f" - P95 Latency: {p95_ms:.2f} ms")

        
        elif res.get("type") == "network":
            # iperf3 JSON structure for sum_sent
            net = res['data']['end']['sum_sent']
            print(f"PROFILE: NETWORK (iperf3)")
            print(f" - Retransmits: {net.get('retransmits', 0)}")
            print(f" - Throughput: {net['bits_per_second']/1e6:.2f} Mbps\n")

if __name__ == "__main__":
    if not os.path.exists('config.json'):
        print("Config file not found.")
        sys.exit(1)
        
    with open('config.json') as f:
        config = json.load(f)

    # STEP 1: VALIDATE
    validate_environment(config)

    # STEP 2: LAUNCH PROCESSES
    q = Queue()
    jobs = [
        Process(target=run_fio, args=("baseline_disk", config['baseline_storage'], q)),
        Process(target=run_fio, args=("custom_proto", config['custom_proto'], q)),
        Process(target=run_fio, args=("oltp", config['oltp'], q)),
        Process(target=run_fio, args=("streaming", config['streaming'], q)),
        Process(target=run_iperf, args=(config['network'], q))
    ]

    for p in jobs: p.start()
    
    # STEP 3: AGGREGATE
    aggregator(q, len(jobs))
    
    for p in jobs: p.join()
