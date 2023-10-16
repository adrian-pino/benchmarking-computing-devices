import subprocess
import os
import configparser
import re
import datetime

def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    
    layers = [layer.strip() for layer in config['general'].get('layers').split(',')]
    variables = {
        "results_file": config['general'].get('results_file', ''),
        "repetitions": int(config['general'].get('repetitions')),
        "duration": int(config['general'].get('duration')),
        "layers": layers
    }

    for layer in layers:
        variables[layer] = {k.replace("_ip", ""): v for k, v in config[layer].items()}

    return variables

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
        file.write("\n".join(results) + "\n\n")

def write_starting_layer_notice(results_file, category):
    with open(results_file, "a") as file:
        file.write(f"[Starting tests for {category.replace('-', ' ').title()}]\n")
        file.write("-----------------------------------\n")

def write_completion_layer_notice(results_file, category):
    with open(results_file, "a") as file:
        file.write("-----------------------------------\n")
        file.write(f"[Completed tests for {category.replace('-', ' ').title()}]\n\n")


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
        for category in config.get('layers', []):
            write_starting_layer_notice(config['results_file'], category)
            for device_name, device_ip in config[category].items():
                successful_pings, total_pings = ping_device(device_ip, config['duration'], config['repetitions'])
                write_service_availability_to_file(config['results_file'], device_name, device_ip, successful_pings, total_pings)
            write_completion_layer_notice(config['results_file'], category)
        print("Script successfully executed. Results stored in: " +config['results_file'])

    except Exception as e:
        print(f"Error: {e}")
