import subprocess
import json
import os
from multiprocessing import Process, Queue

def run_fio(name, params, queue):
    """Worker process to execute FIO with JSON output."""
    cmd = ["fio", "--output-format=json"] + params
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        queue.put({"type": "fio", "name": name, "data": json.loads(result.stdout)})
    except Exception as e:
        queue.put({"name": name, "error": str(e)})

def run_iperf(params, queue):
    """Worker process to execute iperf3 for network baseline."""
    cmd = ["iperf3"] + params
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        queue.put({"type": "network", "name": "iperf_net", "data": json.loads(result.stdout)})
    except Exception as e:
        queue.put({"name": "iperf_net", "error": str(e)})

def aggregator(queue, count):
    """Fourth process: Gathers and analyzes all data."""
    received = 0
    results = []
    while received < count:
        results.append(queue.get())
        received += 1

    print("\n" + "="*50 + "\nFINAL ANALYTICAL REPORT\n" + "="*50)
    for res in results:
        name = res['name']
        if "error" in res:
            print(f"[{name.upper()}] Failed: {res['error']}")
            continue
            
        if res.get("type") == "fio":
            # FIX: Access the first element of the 'jobs' list [0]
            job = res['data']['jobs'][0]
            
            # Aggregate stats (convert KiB to MiB)
            read_bw = job.get('read', {}).get('bw', 0)
            write_bw = job.get('write', {}).get('bw', 0)
            total_bw_mib = (read_bw + write_bw) / 1024
            
            total_iops = job.get('read', {}).get('iops', 0) + job.get('write', {}).get('iops', 0)
            
            # Latency (convert ns to ms)
            # clat_ns is inside 'read' and 'write' separately
            p99_ns = job.get('read', {}).get('clat_ns', {}).get('percentile', {}).get('99.000000', 0)
            p99_ms = p99_ns / 1_000_000

            print(f"PROFILE: {name.upper()}")
            print(f" - Throughput: {total_bw_mib:.2f} MiB/s")
            print(f" - Total IOPS: {total_iops:.0f}")
            print(f" - P99 Latency: {p99_ms:.2f} ms\n")
        
        elif res.get("type") == "network":
            # iperf3 JSON structure
            net = res['data']['end']['sum_sent']
            print(f"PROFILE: NETWORK (iperf3)")
            print(f" - Retransmits: {net.get('retransmits', '0')}")
            print(f" - Throughput: {net['bits_per_second']/1e6:.2f} Mbps\n")

if __name__ == "__main__":
    if not os.path.exists('config.json'):
        print("Config file not found.")
        exit(1)
        
    with open('config.json') as f:
        config = json.load(f)

    q = Queue()
    # List of processes to run simultaneously
    jobs = [
        Process(target=run_fio, args=("baseline", config['baseline'], q)),
        Process(target=run_fio, args=("oltp", config['oltp'], q)),
        Process(target=run_fio, args=("streaming", config['streaming'], q)),
        Process(target=run_iperf, args=(config['network'], q))
    ]

    for p in jobs: p.start()
    aggregator(q, len(jobs))
    for p in jobs: p.join()
