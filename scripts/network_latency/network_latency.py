import subprocess
import os
import configparser
import re
import datetime

def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)

    return {
        "results_file": config['general'].get('results_file', ''),
        "repetitions": int(config['general'].get('repetitions')),
        "duration": int(config['general'].get('duration')),
        "extreme-edge": {k.replace("_ip", ""): v for k, v in config['extreme-edge'].items()},
        "near-edge": {k.replace("_ip", ""): v for k, v in config['near-edge'].items()}
    }

def ping_device(device_ip, duration, repetitions):
    results = []

    for _ in range(repetitions):
        try:
            cmd = ["ping", "-c", str(duration), device_ip]
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            results.append(result)
        except subprocess.CalledProcessError as e:
            results.append(e.output)
    return "\n".join(results)

def filtering_values_from_output(ping_output):
    time_per_second_pattern = re.compile(r"time=([\d.]+) ms")
    rtt_pattern = re.compile(r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms")

    # Split by "--- IP_ADDRESS ping statistics ---" to separate each repetition
    repetitions = re.split(r"--- \d+\.\d+\.\d+\.\d+ ping statistics ---", ping_output)

    times_per_repetition = []
    avg_rtts = []

    for repetition in repetitions:
        if not repetition.strip():
            continue
        
        time_per_second = time_per_second_pattern.findall(repetition)
        times_per_repetition.append([float(time) for time in time_per_second])
        
        avg_match = rtt_pattern.search(repetition)
        if avg_match:
            avg_rtts.append(float(avg_match.group(1)))

    return times_per_repetition, avg_rtts

def write_results_to_file(results_file, device_name, device_ip, ping_output):
    times_per_repetition, avg_rtts = filtering_values_from_output(ping_output)

    with open(results_file, "a") as file:
        file.write("-------------------------\n")
        file.write(f"Device Name: {device_name}\n")
        file.write(f"Device IP: {device_ip}\n\n")

        # Writing each repetition's results
        for index, time_per_second in enumerate(times_per_repetition):
            file.write("Detailed Ping Results for Repetition " + str(index + 1) + ":\n")
            for i, time in enumerate(time_per_second):
                file.write(f"Ping nº{i + 1}: {time:.3f} ms\n")
            file.write("\n")

        # Summary
        file.write("Summary:\n")
        for avg in avg_rtts:
            file.write(f"Average RTT: {avg:.3f} ms\n")
        
        # Total Average
        total_avg_rtt = sum(avg_rtts) / len(avg_rtts) if avg_rtts else 0
        file.write(f"Total Average RTT: {total_avg_rtt:.3f} ms\n\n")

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
            
        # Run the script in the devices specified in the config file
        for category in ['extreme-edge', 'near-edge']:
            for device_name, device_ip in config[category].items():
                ping_results = ping_device(device_ip, config['duration'], config['repetitions'])
                write_results_to_file(config['results_file'], device_name, device_ip, ping_results)
            write_completion_layer_notice(config['results_file'], category)

    except Exception as e:
        print(f"Error: {e}")
