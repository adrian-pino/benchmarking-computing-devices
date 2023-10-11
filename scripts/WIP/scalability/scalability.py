import subprocess
import configparser
import datetime
import os
import socket

def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return {
        "results_file": config['general'].get('results_file', ''),
        "duration": int(config['general'].get('duration')),
        "stress_cpu": int(config['scalability'].get('stress_cpu', 1)),
        "stress_io": int(config['scalability'].get('stress_io', 1)),
        "stress_vm": int(config['scalability'].get('stress_vm', 1)),
        "stress_vm_bytes": config['scalability'].get('stress_vm_bytes', '50M'),
        "threshold": int(config['scalability'].get('threshold', 95))
    }

def stress_system(cpu, io, vm, vm_bytes, duration):
    cmd = [
        "stress",
        "--cpu", str(cpu),
        "--io", str(io),
        "--vm", str(vm),
        "--vm-bytes", vm_bytes,
        "--timeout", str(duration) + "s",
        "--verbose"
    ]
    subprocess.run(cmd)

def capture_vmstat(interval=1, duration=60):
    cmd = ["vmstat", str(interval), str(duration)]
    result = subprocess.check_output(cmd, universal_newlines=True)
    return result.split("\n")[2:-1]

def stress_until_limit(cpu_start=1, io_start=1, vm_start=1, vm_bytes="50M", duration=60, threshold=95):
    max_processes = 0
    while True:
        # Run stress tool
        stress_system(cpu_start, io_start, vm_start, vm_bytes, duration)

        # Get the output of vmstat
        results = capture_vmstat(1, duration)

        # Extract CPU user time from the last line
        cpu_usage = int(results[-1].split()[12])

        # If CPU usage exceeds threshold, break
        if cpu_usage > threshold:
            break

        # Increase the number of processes for the next run
        cpu_start += 1
        io_start += 1
        vm_start += 1
        max_processes += 1

    return max_processes

def write_results_to_file(results_file, hostname, max_processes):
    with open(results_file, "a") as file:
        file.write("-------------------------\n")
        file.write(f"Device name: {hostname}\n\n")
        file.write(f"Maximum number of processes achieved before hitting the threshold: {max_processes}\n\n")

if __name__ == "__main__":
    try:
        config = read_config("config.cfg")

        # Initial info for results file
        script_name = os.path.basename(__file__)
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(config['results_file'], "a") as file:
            file.write(f"Running {script_name} on {current_date}\n")
            file.write(f"{'*' * 60}\n\n")

        # Stress the system until limit and get max processes
        max_processes = stress_until_limit(
            cpu_start=config['stress_cpu'],
            io_start=config['stress_io'],
            vm_start=config['stress_vm'],
            vm_bytes=config['stress_vm_bytes'],
            duration=config['duration'],
            threshold=config['threshold']
        )

        # Write the results to the file
        hostname = socket.gethostname()
        write_results_to_file(config['results_file'], hostname, max_processes)

    except Exception as e:
        print(f"Error: {e}")
