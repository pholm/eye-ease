import requests
import numpy as np
import json
import socket


class TimeSeriesDataProcessor:
    def __init__(self, window_size, alarm_threshold, stress_refil_threshold):
        self.window_size = window_size
        self.alarm_threshold = alarm_threshold
        self.stress_refil_threshold = stress_refil_threshold
        self.left_eye_data = []
        self.right_eye_data = []
        self.due_for_break = False
        self.breakTimer = 0
        self.timeStrech = (
            1000 * 60 * 10
        )  # 10 minutes to begin with, adjust according to person

    def add_data(self, raw_data):
        data = json.loads(raw_data)
        for entry in data:
            self.process_data_entry(entry)

    def process_data_entry(self, entry):
        self._process_eye_data(entry["afe"])

    def _process_eye_data(self, eye_data):
        for eye in eye_data:
            if eye and "m" in eye and eye["m"]:
                signals = eye["m"][0][:6]
                processed_signal = self.complex_analysis(signals)
                eye_list = (
                    self.left_eye_data if eye["t"] == "L" else self.right_eye_data
                )
                eye_list.append(processed_signal)
                # Check the running average after adding new data
                if len(eye_list) >= self.window_size:
                    if self.is_data_alarming(eye_list):
                        self.due_for_break = True
                        self.breakTimer = eye["i"][0]
                if self.due_for_break and (
                    len(eye_list) >= self.stress_refil_threshold
                    or (eye["i"][0] - self.breakTimer > self.timeStrech)
                ):
                    self.alarm()
                    self.due_for_break = False

    def complex_analysis(self, signals):
        weights = np.array([0.3, 0.25, 0.25, 0.1, 0.05, 0.05])
        weighted_avg = np.average(signals, weights=weights)
        std_dev = np.std(signals)
        return weighted_avg - std_dev

    def is_data_alarming(self, eye_data):
        running_avg = (
            np.convolve(eye_data, np.ones(self.window_size), "valid") / self.window_size
        )
        return any(data > self.alarm_threshold for data in running_avg)

    def alarm(self):
        try:
            response = requests.post(
                "https://your-alarm-url.com", json={"alert": "data is alarming"}
            )
            print("Alarm sent, response:", response.status_code)
        except requests.RequestException as e:
            print("Error sending alarm:", e)

    def get_running_average(self, eye):
        data = self.left_eye_data if eye == "L" else self.right_eye_data
        if len(data) < self.window_size:
            return None
        return np.convolve(data, np.ones(self.window_size), "valid") / self.window_size


class SocketListener:
    def __init__(self, host, port, processor):
        self.host = host
        self.port = port
        self.processor = processor
        self.server_socket = None
        self.client_socket = None

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"Listening for connections on {self.host}:{self.port}")

        self.client_socket, addr = self.server_socket.accept()
        print(f"Connection from {addr} has been established.")

        try:
            while True:
                raw_data = self.client_socket.recv(1024)  # Adjust buffer size as needed
                if not raw_data:
                    break
                print("Received data")
                self.processor.add_data(raw_data.decode("utf-8"))
        except OSError:
            pass
        finally:
            self.stop_server()

    def stop_server(self):
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()


if __name__ == "__main__":
    # Tresholds describe how close / far the eye focus is. The straining level is an educated guess based on the data provided
    processor = TimeSeriesDataProcessor(
        window_size=50, alarm_threshold=500, stress_refil_threshold=10000
    )

    # Set up the host and port for the socket server
    host = "127.0.0.1"  # localhost
    port = 12345  # Port to listen on (non-privileged ports are > 1023)

    listener = SocketListener(host, port, processor)
    listener.start_server()
