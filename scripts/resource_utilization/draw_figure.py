import matplotlib.pyplot as plt
import re

def parse_resource_utilization(filename):
    with open(filename, 'r') as file:
        content = file.read()

    device_pattern = re.compile(r"Device name: (.+?)\n\nSummary for .+?:\nAverage CPU User Processes \(us\): ([\d.]+)%\nAverage CPU System Processes \(sy\): ([\d.]+)%\nAverage CPU Idle \(id\): ([\d.]+)%\nAverage Free RAM: ([\d.]+) MB")
    
    results = {}

    for match in device_pattern.findall(content):
        device_name, cpu_us, cpu_sy, cpu_id, ram = match
        if device_name not in results:
            results[device_name] = {
                "cpu_us": [],
                "cpu_sy": [],
                "cpu_id": [],
                "ram": []
            }
        results[device_name]["cpu_us"].append(float(cpu_us))
        results[device_name]["cpu_sy"].append(float(cpu_sy))
        results[device_name]["cpu_id"].append(float(cpu_id))
        results[device_name]["ram"].append(float(ram))

    return results

def plot_cpu_comparison(devices_data, output_file):
    plt.figure(figsize=(12, 7))

    labels = list(devices_data.keys())

    cpu_us_avg = [sum(devices_data[device]['cpu_us']) / len(devices_data[device]['cpu_us']) for device in labels]
    cpu_sy_avg = [sum(devices_data[device]['cpu_sy']) / len(devices_data[device]['cpu_sy']) for device in labels]
    cpu_id_avg = [sum(devices_data[device]['cpu_id']) / len(devices_data[device]['cpu_id']) for device in labels]

    plt.bar(labels, cpu_us_avg, label='CPU User Processes (%)', alpha=0.8, color='purple')
    plt.bar(labels, cpu_sy_avg, bottom=cpu_us_avg, label='CPU System Processes (%)', alpha=0.8, color='green')
    plt.bar(labels, cpu_id_avg, bottom=[i+j for i,j in zip(cpu_us_avg, cpu_sy_avg)], label='CPU Idle (%)', alpha=0.8, color='black')

    plt.title('CPU Usage')
    plt.xlabel('Device')
    plt.ylabel('Percentage (%)')
    plt.legend()
    
    plt.savefig(output_file)
    plt.show()

def plot_ram_comparison(devices_data, output_file):
    plt.figure(figsize=(12, 7))

    labels = list(devices_data.keys())
    ram_avg = [sum(devices_data[device]['ram']) / len(devices_data[device]['ram']) for device in labels]

    plt.bar(labels, ram_avg, color='purple')
    plt.title('RAM Usage')
    plt.xlabel('Device')
    plt.ylabel('Free RAM (MB)')
    
    # Save the figure to the specified file
    plt.savefig(output_file)


if __name__ == "__main__":
    results = parse_resource_utilization("../../results/xgain_testbed_resource_utilization.txt")
    plot_cpu_comparison(results, "../../figures/resource_utilization_cpu.png")
    plot_ram_comparison(results, "../../figures/resource_utilization_ram.png")
