import subprocess
import configparser
import datetime
import os
import socket
import threading
import errno

def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    
    variables = {
        "results_file": config['general'].get('results_file'),
        "repetitions": int(config['general'].get('repetitions')),
        "duration": int(config['general'].get('duration')),
        "vmstat_interval": int(config['resource-utilization'].get('vmstat_interval'))
    }
    return variables

def stress_cpu(duration):
    # fibonacci calculation
    end_time = datetime.datetime.now() + datetime.timedelta(seconds=duration)
    a, b = 0, 1
    while datetime.datetime.now() < end_time:
        a, b = b, a + b

def stress_memory(duration):
    # data structure
    end_time = datetime.datetime.now() + datetime.timedelta(seconds=duration)
    data = []
    while datetime.datetime.now() < end_time:
        try:
            # Append a large number of elements to the list to use up RAM
            data.append([0] * 100)
            
        except MemoryError:
            # Clear the list if a MemoryError occurs (i.e., RAM is full)
            print("RAM is full")
            data.clear()

def memory_string_to_float(mem_str):
    mem_str = mem_str.replace("i", "")  # Strip the 'i' if it exists
    mem_str = mem_str.replace(",", ".")  

    if mem_str[-1] == 'G':
        return float(mem_str[:-1])
    elif mem_str[-1] == 'M':
        return float(mem_str[:-1]) / 1024
    elif mem_str[-1] == 'K':
        return float(mem_str[:-1]) / (1024 ** 2)
    else:
        # Unsupported unit or plain number
        return float(mem_str)

def capture_metrics(vmstat_interval, duration):
    vmstat_cmd = ["vmstat", str(vmstat_interval), str(duration)]
    ram_cmd = ["free", "-h"]

    vmstat_output = subprocess.check_output(vmstat_cmd, universal_newlines=True)
    ram_output = subprocess.check_output(ram_cmd, universal_newlines=True)

    return vmstat_output, ram_output

# Wrapper function to handle results of capture_metrics
def capture_metrics_wrapper(vmstat_interval, duration):
    global vmstat_output, ram_usage  # Or use some shared data structure
    vmstat_output, ram_usage = capture_metrics(vmstat_interval, duration)

def stress_and_capture(vmstat_interval, duration):
    # Threads for each function
    stress_cpu_thread = threading.Thread(target=stress_cpu, args=(duration,))
    stress_memory_thread = threading.Thread(target=stress_memory, args=(duration,))
    capture_metrics_thread = threading.Thread(target=capture_metrics_wrapper, args=(vmstat_interval, duration))

    # Start the threads
    stress_cpu_thread.start()
    stress_memory_thread.start()
    capture_metrics_thread.start()

    # Join the threads (wait for them to finish)
    stress_cpu_thread.join()
    stress_memory_thread.join()
    capture_metrics_thread.join()

    # Assuming you've stored results in some shared data structure or global variable
    # For example:
    # return shared_data["vmstat_output"], shared_data["ram_usage"]
    return vmstat_output, ram_usage  # Modify as per your implementation

def process_metrics(vmstat_output, ram_output):
    # Extract the needed values from the vmstat output
    lines = vmstat_output.split("\n")[2:-1]
    total_us, total_sy, total_id = 0, 0, 0
    for line in lines:
        values = line.split()
        total_us += int(values[12])
        total_sy += int(values[13])
        total_id += int(values[14])
    num_samples = len(lines)

    # Extract used and total memory from the 'free -h' output
    ram_values = ram_output.split('\n')[1].split()
    total_memory = memory_string_to_float(ram_values[1])
    used_memory = memory_string_to_float(ram_values[2])
    ram_usage_percent = (used_memory / total_memory) * 100

    return {
        'avg_us': total_us / num_samples,
        'avg_sy': total_sy / num_samples,
        'avg_id': total_id / num_samples,
        'ram_usage_percent': ram_usage_percent,
        'avg_used_ram_gb': used_memory
    }

def write_results_to_file(results_file, hostname, repetition_number, metrics):
    repetition_number = int(repetition_number) + 1
    with open(results_file, "a") as file:
        file.write(f"Device name: {hostname}\n")
        file.write(f"Repetition number: {repetition_number}\n\n")
        file.write(f"Average CPU User Processes (us): {metrics['avg_us']:.2f}%\n")
        file.write(f"Average CPU System Processes (sy): {metrics['avg_sy']:.2f}%\n")
        file.write(f"Average CPU Idle (id): {metrics['avg_id']:.2f}%\n")
        file.write(f"Average RAM Usage: {metrics['ram_usage_percent']:.2f}%\n")
        file.write(f"Average Used RAM: {metrics['avg_used_ram_gb']:.2f}%\n")


if __name__ == "__main__":
    try:
        config = read_config("config.cfg")

        script_name = os.path.basename(__file__)
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(config['results_file'], "a") as file:
            file.write(f"\n{'*' * 60}\n")
            file.write(f"Running {script_name} on {current_date}\n")
            file.write(f"(Configuration --> Duration: {config['duration']} seconds, Repetitions: {config['repetitions']})\n")
            file.write(f"{'*' * 60}\n")

        for repetition_number in range(config['repetitions']):
            vmstat_output, ram_output = stress_and_capture(
                vmstat_interval=config['vmstat_interval'], 
                duration=config['duration']
            )

            metrics = process_metrics(vmstat_output, ram_output)
            hostname = socket.gethostname()
            write_results_to_file(config['results_file'], hostname, repetition_number, metrics)
            with open(config['results_file'], "a") as file:
                file.write("-----------------------------------\n")
        print("Script successfully executed. Results stored in: " +config['results_file'])

    except Exception as e: 
        print()
        print(f"Error: {e}")
