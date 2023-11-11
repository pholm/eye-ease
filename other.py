import matplotlib.pyplot as plt
import json
import glob
from datetime import timedelta
import numpy as np

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
            entry_labels = ",".join(entry.get("labels", ["noLabel"]))
            previous_labels = (
                all_labels[-1][: len(entry_labels)] if len(all_labels) > 0 else ""
            )
            if len(all_labels) > 0 and entry_labels != previous_labels:
                entry_labels = entry_labels + str(len(all_labels))
                print(
                    "match",
                    entry_labels,
                    previous_labels,
                    entry_labels != previous_labels,
                    all_labels,
                    entry_labels + str(len(all_labels)),
                )
                pass
            if entry_labels not in labels_to_color:
                labels_to_color[entry_labels] = "#%06X" % (
                    0xFFFFFF & hash(entry_labels)
                )
                color_to_label[labels_to_color[entry_labels]] = entry_labels
                all_labels.append(entry_labels)

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
                        "color": labels_to_color[entry_labels],
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
