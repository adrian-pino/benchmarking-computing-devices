import subprocess
import configparser
import datetime
import os
import socket
import threading

def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return {
        "results_file": config['general'].get('results_file', ''),
        "duration": int(config['general'].get('duration')),
        "repetitions": int(config['general'].get('repetitions')),
        "vmstat_interval": int(config['resource-utilization'].get('vmstat_interval')),
        "stress_cpu": int(config['resource-utilization'].get('stress_cpu')),
        "stress_io": int(config['resource-utilization'].get('stress_io')),
        "stress_vm": int(config['resource-utilization'].get('stress_vm')),
        "stress_vm_bytes": config['resource-utilization'].get('stress_vm_bytes'),
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
    print("Executing:", " ".join(cmd))
    subprocess.run(cmd)

def capture_vmstat(interval=1, duration=60):
    cmd = ["vmstat", str(interval), str(duration)]
    result = subprocess.check_output(cmd, universal_newlines=True)
    return result

def process_vmstat_output(device_output):
    lines = device_output.split("\n")[2:-1]
    total_us, total_sy, total_id, total_free = 0, 0, 0, 0

    for line in lines:
        values = line.split()
        if not values[0].isdigit():
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

        metrics = process_vmstat_output(vmstat_output)
        file.write(f"Summary for {hostname}:\n")
        file.write(f"Average CPU User Processes (us): {metrics['avg_us']:.2f}%\n")
        file.write(f"Average CPU System Processes (sy): {metrics['avg_sy']:.2f}%\n")
        file.write(f"Average CPU Idle (id): {metrics['avg_id']:.2f}%\n")  # This line includes the avg_id metric in the results.
        file.write(f"Average RAM Usage: {100 - (metrics['avg_free'] / (os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')) * 100):.2f}%\n")
        file.write(f"Average Free RAM: {metrics['avg_free'] / 1024:.2f} MB\n\n")

def stress_and_capture(vmstat_interval, duration, stress_cpu, stress_io, stress_vm, stress_vm_bytes):
    stress_thread = threading.Thread(target=stress_system, args=(stress_cpu, stress_io, stress_vm, stress_vm_bytes, duration))
    stress_thread.start()

    vmstat_output = capture_vmstat(vmstat_interval, duration)
    stress_thread.join()

    return vmstat_output

if __name__ == "__main__":
    try:
        config = read_config("config.cfg")
        script_name = os.path.basename(__file__)
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(config['results_file'], "a") as file:
            file.write(f"Running {script_name} on {current_date}\n")
            file.write(f"(Configuration --> Duration: {config['duration']} seconds, Repetitions: {config['repetitions']})\n")
            file.write(f"{'*' * 60}\n\n")

        for _ in range(config['repetitions']):
            results = stress_and_capture(
                vmstat_interval=config['vmstat_interval'], 
                duration=config['duration'],
                stress_cpu=config['stress_cpu'], 
                stress_io=config['stress_io'], 
                stress_vm=config['stress_vm'],
                stress_vm_bytes=config['stress_vm_bytes']
            )

            hostname = socket.gethostname()
            write_results_to_file(config['results_file'], hostname, results)

    except Exception as e:
        print(f"Error: {e}")
