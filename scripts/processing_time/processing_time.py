import time
import random
import os
import json
import configparser
from pymongo import MongoClient

# Function to insert data and measure
def insert_data_and_measure(farm_data, mongo_uri, num_repetitions):
    client = MongoClient(mongo_uri)
    db = client[database_name]
    collection = db[collection_name]
    
    success_count = 0
    total_time = 0
    
    for i in range(num_repetitions):
        data_to_insert = random.choice(farm_data)  # Randomly select data
        
        start_time = time.time()
        try:
            collection.insert_one(data_to_insert)
            success_count += 1
        except Exception as e:
            print(f"Error on Farm - Repetition {i + 1}: {e}")
        finally:
            end_time = time.time()
            total_time += end_time - start_time
    
    client.close()
    
    return success_count, total_time / num_repetitions

# Function to read sample data from a JSON file
def read_sample_data(filename):
    with open(filename, "r") as file:
        data = json.load(file)
    return data

# Function to read configuration from the config.cfg file
def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    repetitions = int(config['General']['repetitions'])
    mongodb_port = int(config['General']['mongodb_port'])  # Read MongoDB port setting
    results_folder = config['General']['results_folder']  # Read results folder setting
    
    far_edge_ips = {}
    for key, value in config['far-edge'].items():
        far_edge_ips[key] = value
    
    edge_ips = {}
    for key, value in config['edge'].items():
        edge_ips[key] = value
    
    return repetitions, mongodb_port, results_folder, far_edge_ips, edge_ips

if __name__ == "__main__":
    try:
        # Read configuration from the config.cfg file
        repetitions, mongodb_port, results_folder, far_edge_ips, edge_ips = read_config("config.cfg")
        
        # Read sample data from the JSON file
        farm_data = read_sample_data("sample_agriculture_data.json")
        
        # Create results directory if it doesn't exist
        os.makedirs(results_folder, exist_ok=True)

        for farm in farm_data:
            farm_name = farm["farm_name"]
            
            for device_name, device_ip in far_edge_ips.items():
                mongo_uri = f"mongodb://{device_ip}:{mongodb_port}"  # Include MongoDB port
                success_count, avg_time = insert_data_and_measure(farm_data, mongo_uri, repetitions)
                
                # Write results to a file in the specified results folder
                result_file = os.path.join(results_folder, f"{farm_name}_{device_name}_results.txt")
                with open(result_file, "w") as file:
                    file.write(f"Farm Name: {farm_name}\n")
                    file.write(f"Device Name: {device_name}\n")
                    file.write(f"Device IP: {device_ip}\n")
                    file.write(f"Success Rate: {success_count/repetitions*100:.2f}%\n")
                    file.write(f"Average Insertion Time: {avg_time:.5f} seconds\n")

            for device_name, device_ip in edge_ips.items():
                mongo_uri = f"mongodb://{device_ip}:{mongodb_port}"  # Include MongoDB port
                success_count, avg_time = insert_data_and_measure(farm_data, mongo_uri, repetitions)
                
                # Write results to a file in the specified results folder
                processing_time_results.txt

