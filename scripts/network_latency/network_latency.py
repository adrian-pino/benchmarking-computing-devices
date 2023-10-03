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

def filtering_rtt_from_output(ping_output):
    rtt_pattern = re.compile(r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms")
    avg_rtts = []

    for line in ping_output.splitlines():
        match = rtt_pattern.search(line)
        if match:
            avg_rtt = float(match.group(1))  # Convert string to float
            avg_rtts.append(avg_rtt)

    return avg_rtts

def write_results_to_file(results_file, device_name, device_ip, ping_output):
    avg_rtts = filtering_rtt_from_output(ping_output)

    # Calculate the total average RTT
    total_avg_rtt = sum(avg_rtts) / len(avg_rtts) if avg_rtts else 0

    results = [
        f"Device Name: {device_name}",
        f"Device IP: {device_ip}",
    ]
    # results.extend([f"Average RTT: {rtt} ms" for rtt in avg_rtts])
    results.append(f"\nTotal Average RTT: {total_avg_rtt:.3f} ms")

    # Write the results to a file
    with open(results_file, "a") as file:
        file.write("-------------------------\n")
        file.write("\n".join(results) + "\n\n")


if __name__ == "__main__":
    try:
        config = read_config("config.cfg")

        # Write the initial lines to the results file
        script_name = os.path.basename(__file__)
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(config['results_file'], "a") as file:
            file.write(f"Running {script_name} on {current_date}\n")
            file.write(f"(Configuration --> Duration: {config['duration']} seconds, Repetitions: {config['repetitions']})\n\n")

        # Run the script in the devices specified in the config file
        for category in ['extreme-edge', 'near-edge']:
            for device_name, device_ip in config[category].items():
                ping_results = ping_device(device_ip, config['duration'], config['repetitions'])
                write_results_to_file(config['results_file'], device_name, device_ip, ping_results)

    except Exception as e:
        print(f"Error: {e}")
