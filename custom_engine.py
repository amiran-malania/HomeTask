import subprocess
import json

def run_custom_fio_test(engine_path, protocol_target, block_size="4k"):
    """
    Executes fio using a custom external I/O engine.
    """
    # Define the fio command using the 'external' engine flag
    command = [
        "fio",
        "--name=custom_protocol_test",
        f"--ioengine=external:{engine_path}",  # Points to your custom protocol .so
        f"--filename={protocol_target}",       # The target (IP, device path, etc.)
        f"--bs={block_size}",
        "--rw=randwrite",
        "--size=1G",
        "--io_size=1G",
        "--iodepth=32",
        "--runtime=30",
        "--time_based",
        "--output-format=json"                 # Get results in a parsable format
    ]

    print(f"Starting test on {protocol_target} using {engine_path}...")
    
    try:
        # Run the command and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Extract specific performance metrics
        write_iops = data['jobs'][0]['write']['iops']
        print(f"Test Complete! IOPS achieved: {write_iops}")
        
    except subprocess.CalledProcessError as e:
        print(f"Fio failed: {e.stderr}")


def main():
    #"--ioengine=external:/Users/abstraction_builder/Projects/Virtuozzo/the_best_protocol_ever.so"
    path_to_engine = "/Users/abstraction_builder/Projects/Virtuozzo/the_best_protocol_ever.dylib"
    target = "127.0.0.1" 
    run_custom_fio_test(path_to_engine, target)

if __name__ == '__main__':
    main()