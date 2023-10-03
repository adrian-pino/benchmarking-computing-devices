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
    successful_pings = 0
    total_pings = duration * repetitions

    for _ in range(repetitions):
        try:
            cmd = ["ping", "-c", str(duration), device_ip]
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            successful_pings += result.count("bytes from")
        except subprocess.CalledProcessError as e:
            pass  # Assume no successful pings if there's an error

    return successful_pings, total_pings

def calculate_service_availability(successful_pings, total_pings):
    if total_pings == 0:
        return 0  # To avoid division by zero
    return (successful_pings / total_pings) * 100


def write_service_availability_to_file(results_file, device_name, device_ip, successful_pings, total_pings):
    availability = calculate_service_availability(successful_pings, total_pings)
    results = [
        f"Device Name: {device_name}",
        f"Device IP: {device_ip}",
        f"Service Availability: {availability:.2f}%",
        f"Successful Pings: {successful_pings}",
        f"Total Pings: {total_pings}",
    ]

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
                successful_pings, total_pings = ping_device(device_ip, config['duration'], config['repetitions'])
                write_service_availability_to_file(config['results_file'], device_name, device_ip, successful_pings, total_pings)

    except Exception as e:
        print(f"Error: {e}")
