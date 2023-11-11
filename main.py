import matplotlib.pyplot as plt
import json
import glob
from datetime import timedelta


ticktime = []
ambient_light_values = []

for filename in glob.glob('./secrets/Indoor/Participant_1/AFE_*.json'):
    with open(filename, 'r') as file:
        # Parse the JSON data
        data = json.load(file)

    for entry in data:
        # Extracting 'ticktime' and 'Ambient Light' value
        # Convert milliseconds to seconds
        tick_time_seconds = entry['auxSensors']['lightAmbient']['i'][0] / 1000
        formatted_time = str(timedelta(seconds=tick_time_seconds))[
            2:7]  # Format as mm:ss
        # Ambient Light value
        ambient_light_value = entry['auxSensors']['lightAmbient']['v'][2]

        ticktime.append(formatted_time)
        ambient_light_values.append(ambient_light_value)

# Create a plot
plt.figure(figsize=(10, 6))
plt.plot(ticktime, ambient_light_values, marker='o')
plt.xlabel('Ticktime (mm:ss)')
plt.ylabel('Ambient Light Value')
plt.title('Ambient Light Values over Time')
plt.xticks(rotation=45)
plt.grid(True)
plt.show()
