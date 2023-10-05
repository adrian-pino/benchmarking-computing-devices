import time
import random
import os
import json
import configparser
from pymongo import MongoClient
import datetime

def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)

    return {
        "mongodb_port": int(config['general'].get('mongodb_port')),
        "results_file": config['general'].get('results_file', ''),
        "repetitions": int(config['general'].get('repetitions')),
        "database_name": config['general'].get('database_name', ''),
        "collection_name": config['general'].get('collection_name', ''),
        "extreme-edge": {k.replace("_ip", ""): v for k, v in config['extreme-edge'].items() if not k.startswith('#') and k.endswith('_ip')},
        "near-edge": {k.replace("_ip", ""): v for k, v in config['near-edge'].items() if not k.startswith('#') and k.endswith('_ip')}
    }

def get_mongo_client(device_ip, port, database_name):
    try:
        client = MongoClient(device_ip, port)
        db = client[database_name]
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB at {device_ip}:{port}. Error: {e}")
        return None

def read_json_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def measure_insertion_time(db, collection_name, data, repetitions):
    collection = db[collection_name]
    
    total_successful_inserts = 0
    total_failed_inserts = 0

    start_time = time.time()
    for _ in range(repetitions):
        try:
            result = collection.insert_many(data, ordered=False)
            total_successful_inserts += len(result.inserted_ids)
        except Exception as e:
            # When using ordered=False, BulkWriteError is raised for failed inserts.
            # The details of the failed inserts can be found in the 'writeErrors' attribute.
            if hasattr(e, 'details') and 'writeErrors' in e.details:
                total_failed_inserts += len(e.details['writeErrors'])
    end_time = time.time()

    total_attempts = len(data) * repetitions
    success_rate = (total_successful_inserts / total_attempts) * 100
    
    avg_insertion_time = (end_time - start_time) / repetitions

    return avg_insertion_time, success_rate

def drop_collection(db, collection_name):
    try:
        db.drop_collection(collection_name)
        print(f"Collection '{collection_name}' dropped successfully.")
    except Exception as e:
        print(f"Error dropping collection '{collection_name}': {e}")

def write_processing_time_to_file(results_file, device_name, device_ip, avg_insertion_time, success_rate):
    results = [
        f"Device Name: {device_name}",
        f"Device IP: {device_ip}",
        f"Average Insertion Time: {avg_insertion_time:.3f} seconds",
        f"Success Rate: {success_rate}%"
    ]

    with open(results_file, "a") as file:
        file.write("-------------------------\n")
        file.write("\n".join(results) + "\n\n")

def write_completion_layer_notice(results_file, category):
    with open(results_file, "a") as file:
        file.write("\n" + ('*' * 40) + "\n")
        file.write(f"Completed tests for {category.replace('-', ' ').title()}\n")
        file.write(('*' * 40) + "\n\n")


if __name__ == "__main__":
    try:
        config = read_config("config.cfg")
        # json_data = read_json_file(config['db_file'])
        json_data = read_json_file("sample_agriculture_data.json") # TODO: hardcoded

         # Write the initial lines to the results file
        script_name = os.path.basename(__file__)
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(config['results_file'], "a") as file:
            file.write(f"Running {script_name} on {current_date}\n")
            file.write(f"(Configuration --> Duration: {config['duration']} seconds, Repetitions: {config['repetitions']})\n")
            file.write(f"{'*' * 60}\n\n")

        # Run the script for the devices specified in the config file
        for category in ['extreme-edge', 'near-edge']:
            for device_name, device_ip in config[category].items():
                db = get_mongo_client(device_ip, config['mongodb_port'], config['database_name'])
                
                if db is None:
                    print(f"Skipping {device_name} due to connection issues.")
                    continue  # Skip the rest of the loop for this device
                
                avg_insertion_time, success_rate = measure_insertion_time(db, config['collection_name'], json_data, config['repetitions'])
                write_processing_time_to_file(config['results_file'], device_name, device_ip, avg_insertion_time, success_rate)
                drop_collection(db, config['collection_name'])
            write_completion_layer_notice(config['results_file'], category)

    except Exception as e:
        print(f"Error: {e}")
