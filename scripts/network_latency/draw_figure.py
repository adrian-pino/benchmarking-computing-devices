import matplotlib.pyplot as plt
import re
import configparser

def parse_results(filename):
    with open(filename, 'r') as file:
        content = file.read()

    # Extract the device name and their results
    device_pattern = re.compile(r"Device Name: (.+?)\nDevice IP: .+?\n\n(.*?)\n\nSummary:", re.DOTALL)
    ping_pattern = re.compile(r"Ping nº\d+: ([\d.]+) ms")

    results = {}

    for match in device_pattern.findall(content):
        device_name, pings_data = match
        pings = [float(ping) for ping in ping_pattern.findall(pings_data)]
        results[device_name] = pings

    return results

def plot_results(devices_data, output_file):
    plt.figure(figsize=(12, 7))

    labels = list(devices_data.keys())
    averages = [sum(devices_data[device])/len(devices_data[device]) for device in labels]
    color_palette = plt.cm.viridis  # Using the viridis colormap, but you can choose another if you prefer

    bars = plt.bar(labels, averages, color=[color_palette(i) for i in range(len(averages))])

    # Add data values on top of each bar
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.01, round(yval, 2), ha='center', va='bottom')

    plt.title('Network Latency')  # Adjusted the title as per your request
    plt.xlabel('Device')  # Label for the devices
    plt.ylabel('Average Network Latency (ms)')  # Adjusted the y-axis label as per your request
    plt.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5)

    # Save the figure to the specified file
    plt.savefig(output_file)

    # Display the figure
    plt.show()


if __name__ == "__main__":
    results = parse_results('../../results/xgain_testbed_network_latency.txt')
    plot_results(results, "../../figures/network_latency.png")
