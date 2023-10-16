# Benchmarking computing devices

Repository containing python scripts to perform a benchmarking on the compute segment of the network.

## Requirements

Before you begin, ensure you have met the following requirements:

- [Python 3](https://www.python.org/downloads/)
- [venv (Python Virtual Environment)](https://docs.python.org/3/library/venv.html)

## Setup

Follow these steps to set up your project environment:

1. Create a virtual environment named "venv-xgain" using `venv`:

    ```bash
    python3 -m venv venv-xgain
    ```

2. Activate the virtual environment:

    On Linux:

    ```bash
    source venv-xgain/bin/activate
    ```

3. Navigate to the KPI folder to be measured (under scripts folder).
- Set the configuration file.
- Install the requirements specified in scripts/KPI_NAME/requirements.txt if any.
- Run the python script with the KPI name.

e.g:
   ```bash
    cd scripts/network_latency
    (venv-xgain) python network_latency.py
   ```
