import matplotlib.pyplot as plt
import json
import glob
from datetime import timedelta


ticktime = []
labels = []

for filename in glob.glob('./secrets/Indoor/Participant_1/AFE_*.json'):
    with open(filename, 'r') as file:
        # Parse the JSON data
        data = json.load(file)

        for entry in data:
            # Check if 'labels' key exists in the entry
            if 'labels' in entry:
                # Convert ticktime to mm:ss format
                # Convert milliseconds to seconds
                tick_time_seconds = entry['auxSensors']['tempEt']['i'][0] / 1000
                formatted_time = str(timedelta(seconds=tick_time_seconds))[
                    2:7]  # Format as mm:ss
                ticktime.append(formatted_time)
                # Using 'tempEt' ticktime as an example
                labels.extend(entry['labels'])

# To plot, we need to map non-numeric labels to numbers
unique_labels = list(set(labels))
label_mapping = {label: i for i, label in enumerate(unique_labels)}

# Map the labels to numbers
mapped_labels = [label_mapping[label] for label in labels]

# Create a scatter plot
plt.figure(figsize=(15, 6))  # Increase figure size
plt.scatter(ticktime, mapped_labels)


# Display fewer x-axis labels
# plt.xticks(ticks=plt.xticks()[0], labels=ticktime[::len(ticktime)//10])


plt.yticks(range(len(unique_labels)), unique_labels)
plt.xlabel('Ticktime (mm:ss)')
plt.ylabel('Labels')
plt.title('Labels over Ticktime')
plt.xticks(rotation=45)  # Rotate x-axis labels for better visibility
plt.grid(True)
plt.show()
