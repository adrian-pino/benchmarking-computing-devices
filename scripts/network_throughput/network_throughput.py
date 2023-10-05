import subprocess
import os
import configparser
import re
import datetime
import pdb

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

def measure_throughput(server_ip, duration, repetitions):
    results = []

    for _ in range(repetitions):
        try:
            cmd = ["iperf3", "-c", server_ip, "-t", str(duration)]
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            results.append(result)
        except subprocess.CalledProcessError as e:
            results.append(e.output)
    return "\n".join(results)

# TODO Fix regex pattern
# def extract_bandwidth_from_output(iperf_output):
#     bandwidth_pattern = re.compile(r"\[\s+\d+\]\s+\d+\.\d+-\d+\.\d+\s+sec\s+\d+\s+\w+Bytes\s+(\d+\.\d+)\s+(\wbits/sec)\s+receiver")
#     bandwidths = []
    
#     for line in iperf_output.splitlines():
#         match = bandwidth_pattern.search(line)
#         if match:
#             value, unit = float(match.group(1)), match.group(2)

#             # Convert to Mbits/sec if necessary
#             if unit == "Kbits/sec":
#                 value /= 1000
#             elif unit == "Gbits/sec":
#                 value *= 1000
#             # Add other potential conversions if needed

#             # pdb.set_trace()

#             bandwidths.append(value)

#     return bandwidths
    
def write_results_to_file(results_file, device_name, device_ip, iperf_output):
    # bandwidths = extract_bandwidth_from_output(iperf_output)
    # bandwidths = iperf_output
    # total_avg_bandwidth = sum(bandwidths) / len(bandwidths) if bandwidths else 0

    # results = [
    #     f"Device Name: {device_name}",
    #     f"Device IP: {device_ip}",
    # ]
    # results.append(f"\nTotal Average Bandwidth: {total_avg_bandwidth:.3f} Mbits/sec")

    # with open(results_file, "a") as file:
    #     file.write("-------------------------\n")
    #     file.write("\n".join(results) + "\n\n")

    with open(results_file, "a") as file:
        file.write("-------------------------\n")
        # file.write("\n".join(results) + "\n\n")
        file.write(f"Device Name: {device_name}\n")
        file.write(f"Device IP: {device_ip}\n")
        file.write(iperf_output)

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
                throughput_results = measure_throughput(device_ip, config['duration'], config['repetitions'])
                write_results_to_file(config['results_file'], device_name, device_ip, throughput_results)
            write_completion_layer_notice(config['results_file'], category)

    except Exception as e:
        print(f"Error: {e}")
