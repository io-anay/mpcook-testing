import psutil
import time
import threading
import matplotlib.pyplot as plt
import subprocess
import os
import json
import numpy as np

# Lists to store usage data
cpu_usage = []
memory_usage = []

baseline_cpu = 0
baseline_memory = 0

def monitor_baseline_usage(time_ms, inc_ms=1000):
    # Monitor CPU and memory usage for the specified time recording the data every inc ms
    cpu_usage.clear()
    memory_usage.clear()
    for i in range(time_ms // inc_ms):
        cpu_usage.append(psutil.cpu_percent())
        memory_usage.append(psutil.virtual_memory().percent)
        time.sleep(inc_ms / 1000)

    # Store the baseline CPU and memory usage
    baseline_cpu = sum(cpu_usage) / len(cpu_usage)
    baseline_memory = sum(memory_usage) / len(memory_usage)

    print("\n===================")
    print("Baseline CPU usage: " + str(baseline_cpu) + "%")
    print("Baseline memory usage: " + str(baseline_memory) + "%")
    print("===================\n")

    return baseline_cpu, baseline_memory

def monitor_usage(command, root, output_file, index=0):
    cpu_usage.clear()
    memory_usage.clear()

    print("\n>> Running: " + ' '.join(command))

    # Run the command as a subprocess. While the command is running loop and collect usage data every second
    process = subprocess.Popen(command, shell=True, stdout=open(output_file, 'w'))
    while process.poll() is None:
        cpu_usage.append((time.time(), psutil.cpu_percent()))
        memory_usage.append((time.time(), psutil.virtual_memory().percent))

        # Write the data to file every 10 seconds
        if len(cpu_usage) % 10 == 0:
            with open(os.path.join(root, f'usage_data_{index}.json'), 'w') as f:
                json.dump({"cpu_usage": cpu_usage, "memory_usage": memory_usage}, f)

        time.sleep(1)

    # Write any remaining data points to the file
    with open(os.path.join(root, f'usage_data_{index}.json'), 'w') as f:
        json.dump({"cpu_usage": cpu_usage, "memory_usage": memory_usage}, f)

    return process

def plot_usage(cpu_usage, memory_usage, baseline_cpu, baseline_memory):
    # Plot the CPU usage
    plt.plot([x[0] for x in cpu_usage], [x[1] for x in cpu_usage], label="CPU usage")
    plt.plot([x[0] for x in cpu_usage], [baseline_cpu for x in cpu_usage], label="Baseline CPU usage")
    plt.xlabel("Time (s)")
    plt.ylabel("CPU usage (%)")
    plt.legend()
    plt.show()

    # Plot the memory usage
    plt.plot([x[0] for x in memory_usage], [x[1] for x in memory_usage], label="Memory usage")
    plt.plot([x[0] for x in memory_usage], [baseline_memory for x in memory_usage], label="Baseline memory usage")
    plt.xlabel("Time (s)")
    plt.ylabel("Memory usage (%)")
    plt.legend()
    plt.show()

def moving_average(data, window_size):
    # Calculate the moving average of the data
    return np.convolve(data, np.ones(window_size), 'valid') / window_size

def plot_smoothed_data(json_files, title, root, window_size=5, baseline_cpu=0, baseline_memory=0):
    plt.figure()

    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)

        cpu_usage = data['cpu_usage']
        memory_usage = data['memory_usage']

        # Convert cpu_times from time since epoch to time since start of command
        cpu_times = [x[0] - cpu_usage[0][0] for x in cpu_usage]
        memory_times = [x[0] - memory_usage[0][0] for x in memory_usage]

        # cpu_times = [x[0] for x in cpu_usage]
        cpu_values = [x[1] for x in cpu_usage]
        # memory_times = [x[0] for x in memory_usage]
        memory_values = [x[1] for x in memory_usage]

        smoothed_cpu_values = moving_average(cpu_values, window_size)
        smoothed_memory_values = moving_average(memory_values, window_size)

        plt.plot(cpu_times[window_size - 1:], smoothed_cpu_values, 'b')
        plt.plot(memory_times[window_size - 1:], smoothed_memory_values, 'r')

    # plot the baselines if they have been provided and are non zero from 0 to the largest time we recorded
    if baseline_cpu != 0:
        plt.plot([0, max(cpu_times)], [baseline_cpu, baseline_cpu], 'b--')
    if baseline_memory != 0:
        plt.plot([0, max(memory_times)], [baseline_memory, baseline_memory], 'r--')

    plt.title(title)

    plt.xlabel('Time (s)')
    plt.ylabel('Usage (%)')
    plt.savefig(os.path.join(root, 'usage_plot.png'))
