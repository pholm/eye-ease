import matplotlib.pyplot as plt
import json
import glob
from datetime import timedelta
import numpy as np
import random

# Initialize data structures
left_eye_data = []
right_eye_data = []
all_labels = []
labels_to_color = {}
color_to_label = {}

# Process each file
for filename in glob.glob("./secrets/Indoor/Participant_1/AFE_*.json"):
    with open(filename, "r") as file:
        data = json.load(file)

        for entry in data:
            # Handle labels and colors
            entry_label = entry.get("labels", ["noLabel"])[0]
            previous_label = (
                all_labels[-1][: len(entry_label)] if len(all_labels) > 0 else ""
            )
            if len(all_labels) > 0 and entry_label != previous_label:
                print(
                    "match",
                    entry_label,
                    previous_label,
                    entry_label != previous_label,
                    all_labels,
                    entry_label + str(len(all_labels)),
                )
                ## entry label should stay the same, unless it exists in the all_labels, then it should be the number of the labels in all labels that share the base form
                baseForm = entry_label
                entry_label = baseForm  # if something
            if entry_label not in labels_to_color:
                labels_to_color[entry_label] = "#%06X" % (
                    0xFFFFFF & hash(random.randint(0, 1000000))
                )
                color_to_label[labels_to_color[entry_label]] = entry_label
                all_labels.append(entry_label)
                print(entry_label, "new color", labels_to_color[entry_label])

            # Process eye data
            for eye in entry["afe"]:
                if eye:  # Check if eye_data is not empty
                    average = (
                        sum(eye["m"][0][:6]) / len(eye["m"][0][:6])
                        if eye["m"][0]
                        else 0
                    )
                    tick_time_ms = eye["i"][0]
                    tick_time_seconds = tick_time_ms / 1000
                    formatted_time = str(timedelta(seconds=tick_time_seconds))[2:7]

                    data_point = {
                        "time": formatted_time,
                        "average": average,
                        "color": labels_to_color[entry_label],
                    }

                    # Append data to the correct list
                    if eye["t"] == "L":
                        left_eye_data.append(data_point)
                    elif eye["t"] == "R":
                        right_eye_data.append(data_point)


# Function to plot data for an eye
def plot_eye_data(eye_data, eye_label):
    times = [dp["time"] for dp in eye_data]
    averages = [dp["average"] for dp in eye_data]
    colors = [dp["color"] for dp in eye_data]

    # Plot each segment with its color
    for i in range(len(times) - 1):
        plt.plot(
            times[i : i + 2],
            averages[i : i + 2],
            color=colors[i],
            label=f"{eye_label} Eye ({times[i]} - {times[i+1]})",
        )


def calculate_rolling_average(data, window_size):
    averages = np.array([dp["average"] for dp in data])
    rolling_avg = np.convolve(averages, np.ones(window_size), "valid") / window_size
    # Adjust times to match the length of rolling averages
    adjusted_times = [
        data[i + window_size - 1]["time"] for i in range(len(data) - window_size + 1)
    ]
    return adjusted_times, rolling_avg


def plot_eye_data_by_color(eye_data, eye_label, window_size, y_offset=0, linestyle="-"):
    unique_colors = set(dp["color"] for dp in eye_data)
    for color in unique_colors:
        label = color_to_label[color]
        filtered_data = [dp for dp in eye_data if dp["color"] == color]
        times, rolling_averages = calculate_rolling_average(filtered_data, window_size)

        if len(times) == 0 or len(rolling_averages) == 0:
            continue  # Skip plotting if there are no data points or if rolling average could not be calculated

        # Apply offset to y-values
        rolling_averages += y_offset
        plt.plot(
            times,
            rolling_averages,
            label=f"{eye_label} Eye - {label}",
            color=color,
            linestyle=linestyle,
        )


# Your existing code for plotting


# Choose an appropriate window size for rolling average
window_size = 50  # Example size, adjust as needed

# Plotting with rolling average
plt.figure(figsize=(15, 6))
plot_eye_data_by_color(left_eye_data, "Left", window_size, linestyle="-")
plot_eye_data_by_color(right_eye_data, "Right", window_size, y_offset=0, linestyle="--")

plt.xlabel("Time (mm:ss)")
plt.ylabel("Average Signal Value (Rolling Average)")
plt.title("Rolling Average Strain Over Time")
plt.xticks(rotation=45)
plt.legend()
plt.show()
