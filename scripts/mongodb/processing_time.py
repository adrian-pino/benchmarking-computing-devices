import time
import random
import os
import json
import configparser
from pymongo import MongoClient

# Define the database name and collection name
database_name = "benchmarking-computing"
collection_name = "farms"

# Function to insert data and measure
def insert_data_and_measure(farm_data, mongo_uri, num_repetitions):
    print(f"Connecting to MongoDB at {mongo_uri} on device {device_name}")  # Print the connection information
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
    repetitions = int(config['general']['repetitions'])
    mongodb_port = int(config['general']['mongodb_port'])  # Read MongoDB port setting
    results_folder = config['general']['results_folder']  # Read results folder setting
    
    far_edge_ips = {}
    for key, value in config['far-edge'].items():
        far_edge_ips[key] = value
    
    edge_ips = {}
    for key, value in config['edge'].items():
        edge_ips[key] = value
    
    return repetitions, mongodb_port, results_folder, far_edge_ips, edge_ips

if __name__ == "__main__":
    try:
        script_name = os.path.basename(__file__)
        print(f"Executing script: {script_name}")
        print("**************************************************************************************************************")
        print("This script inserts data into different MongoDBs databases placed on different devices and measures performance.")


        # Read configuration from the config.cfg file
        repetitions, mongodb_port, results_folder, far_edge_ips, edge_ips = read_config("config.cfg")

        # Read sample data from the JSON file
        farm_data = read_sample_data("sample_agriculture_data.json")

        # Create a dictionary to store results
        results_dict = {}

        print(f"Results will be stored in the folder: {results_folder}")
        print("Results include success rates and average insertion times for different devices.")
        print("**************************************************************************************************************")

        for farm in farm_data:
            farm_name = farm["farm_name"]

            # Create sub-dictionaries for each farm
            farm_results = {"far_edge": {}, "edge": {}}

            for device_name, device_ip in far_edge_ips.items():
                mongo_uri = f"mongodb://{device_ip}:{mongodb_port}"  # Include MongoDB port
                success_count, avg_time = insert_data_and_measure(farm_data, mongo_uri, repetitions)

                # Store results for far-edge devices
                farm_results["far_edge"][device_name] = {
                    "Device IP": device_ip,
                    "Success Rate": success_count / repetitions * 100,
                    "Average Insertion Time": avg_time,
                }

            for device_name, device_ip in edge_ips.items():
                mongo_uri = f"mongodb://{device_ip}:{mongodb_port}"  # Include MongoDB port
                success_count, avg_time = insert_data_and_measure(farm_data, mongo_uri, repetitions)

                # Store results for edge devices
                farm_results["edge"][device_name] = {
                    "Device IP": device_ip,
                    "Success Rate": success_count / repetitions * 100,
                    "Average Insertion Time": avg_time,
                }

            # Store farm-specific results in the main results dictionary
            results_dict[farm_name] = farm_results

        # Save the results dictionary as a JSON file
        results_file = os.path.join(results_folder, "results.json")
        with open(results_file, "w") as json_file:
            json.dump(results_dict, json_file, indent=4)

        print("Results saved to results.json")

    except Exception as e:
        print(f"An error occurred: {e}")
