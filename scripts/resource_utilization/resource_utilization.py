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
        "repetitions": int(config['general'].get('repetitions')),
        "vmstat_interval": int(config['resource-utilization'].get('vmstat_interval', 1)),
        "stress_cpu": int(config['resource-utilization'].get('stress_cpu', 1)),
        "stress_io": int(config['resource-utilization'].get('stress_io', 1)),
        "stress_vm": int(config['resource-utilization'].get('stress_vm', 1)),
        "stress_vm_bytes": config['resource-utilization'].get('stress_vm_bytes', '50M'),
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
    return result

def process_vmstat_output(device_output):
    # Extract lines corresponding to the vmstat results
    lines = device_output.split("\n")[2:-1]

    # Initialize metrics
    total_us, total_sy, total_id, total_free = 0, 0, 0, 0

    # Iterate through each line to compute averages
    for line in lines:
        values = line.split()
        if not values[0].isdigit():  # Skip lines that don't start with a number
            continue
        total_us += int(values[12])
        total_sy += int(values[13])
        total_id += int(values[14])
        total_free += int(values[3])

    num_samples = len(lines)
    return {
        'avg_us': total_us / num_samples,
        'avg_sy': total_sy / num_samples,
        'avg_id': total_id / num_samples,
        'avg_free': total_free / num_samples
    }

def write_results_to_file(results_file, hostname, vmstat_output):
    with open(results_file, "a") as file:
        file.write("-------------------------\n")
        file.write(f"Device name: {hostname}\n\n")

        # Writing the vmstat results directly
        file.write("Resource Utilization:\n")
        file.write(vmstat_output + "\n\n")

        # Extract metrics from vmstat_output
        metrics = process_vmstat_output(vmstat_output)

        # Append the summary
        file.write(f"Summary for {hostname}:\n")
        file.write(f"Average CPU User Processes (us): {metrics['avg_us']:.2f}%\n")
        file.write(f"Average CPU System Processes (sy): {metrics['avg_sy']:.2f}%\n")
        file.write(f"Average CPU Idle (id): {metrics['avg_id']:.2f}%\n")
        file.write(f"Average Free RAM: {metrics['avg_free'] / 1024:.2f} MB\n\n")

def write_completion_layer_notice(results_file, category):
    with open(results_file, "a") as file:
        file.write("\n" + ('*' * 40) + "\n")
        file.write(f"Completed tests for {category.replace('-', ' ').title()}\n")
        file.write(('*' * 40) + "\n\n")


if __name__ == "__main__":
    try:
        config = read_config("config.cfg")

        # Write the initial lines to the results file
        script_name = os.path.basename(__file__)
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(config['results_file'], "a") as file:
            file.write(f"Running {script_name} on {current_date}\n")
            file.write(f"(Configuration --> Duration: {config['duration']} seconds, Repetitions: {config['repetitions']})\n")
            file.write(f"{'*' * 60}\n\n")

        for _ in range(config['repetitions']):
            # Start stressing the system
            stress_system(
                cpu=config['stress_cpu'], 
                io=config['stress_io'], 
                vm=config['stress_vm'],
                vm_bytes=config['stress_vm_bytes'],
                duration=config['duration']
            )
            
            # Capture resource utilization metrics
            results = capture_vmstat(
                interval=config['vmstat_interval'], 
                duration=config['duration']
            )
            
            # Write the results to the file
            hostname = socket.gethostname()
            write_results_to_file(config['results_file'], hostname, results)

    except Exception as e:
        print(f"Error: {e}")