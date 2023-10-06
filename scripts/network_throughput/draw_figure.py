import matplotlib.pyplot as plt
import re

def parse_throughput(filename):
    with open(filename, 'r') as file:
        content = file.read()

    # Extract the device name and their throughput results
    device_pattern = re.compile(r"Device Name: (.+?)\nDevice IP: .+?\n(.*?)\niperf Done\.", re.DOTALL)
    throughput_pattern = re.compile(r"\[\s+\d\]\s+\d+\.\d{2}-\d+\.\d{2}\s+sec\s+\d+\sMBytes\s+(\d{3,4})\sMbits/sec")

    results = {}

    for match in device_pattern.findall(content):
        device_name, throughput_data = match
        throughputs = [float(throughput) for throughput in throughput_pattern.findall(throughput_data)]
        # Assuming you want to average the throughputs for each device's tests:
        avg_throughput = sum(throughputs) / len(throughputs)
        results[device_name] = avg_throughput

    return results

def plot_throughput(devices_data, output_file):
    plt.figure(figsize=(12, 7))

    labels = list(devices_data.keys())
    throughputs = [devices_data[device] for device in labels]
    color_palette = plt.cm.viridis

    bars = plt.bar(labels, throughputs, color=[color_palette(i) for i in range(len(throughputs))])

    # Add data values on top of each bar
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 5, round(yval, 2), ha='center', va='bottom')

    plt.title('Network Throughput')
    plt.xlabel('Device')
    plt.ylabel('Average Throughput (Mbits/sec)')
    plt.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5)

    # Save the figure to the specified file
    plt.savefig(output_file)

    # Display the figure
    plt.show()

if __name__ == "__main__":
    results = parse_throughput('../../results/xgain_testbed_network_throughput.txt')
    plot_throughput(results, "../../figures/network_throughput.png")
