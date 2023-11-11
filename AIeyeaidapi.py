import bluetooth
import numpy as np
import json


class TimeSeriesDataProcessor:
    def __init__(self, window_size):
        self.window_size = window_size
        self.left_eye_data = []
        self.right_eye_data = []

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
                average_signal = sum(signals) / len(signals)
                if eye["t"] == "L":
                    self.left_eye_data.append(average_signal)
                elif eye["t"] == "R":
                    self.right_eye_data.append(average_signal)

    def get_running_average(self, eye):
        data = self.left_eye_data if eye == "L" else self.right_eye_data
        if len(data) < self.window_size:
            return None
        return np.convolve(data, np.ones(self.window_size), "valid") / self.window_size


class BluetoothListener:
    def __init__(self, uuid, service_name, processor):
        self.uuid = uuid
        self.service_name = service_name
        self.processor = processor
        self.server_sock = None
        self.client_sock = None

    def start_server(self):
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("", bluetooth.PORT_ANY))
        self.server_sock.listen(1)
        bluetooth.advertise_service(
            self.server_sock,
            self.service_name,
            service_id=self.uuid,
            service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
            profiles=[bluetooth.SERIAL_PORT_PROFILE],
        )
        print("Waiting for connection on RFCOMM channel")
        self.client_sock, client_info = self.server_sock.accept()
        print(f"Accepted connection from {client_info}")

        try:
            while True:
                raw_data = self.client_sock.recv(1024)  # Adjust buffer size as needed
                if not raw_data:
                    break
                print("Received data")
                self.processor.add_data(raw_data.decode("utf-8"))
        except OSError:
            pass
        finally:
            self.stop_server()

    def stop_server(self):
        if self.client_sock:
            self.client_sock.close()
        if self.server_sock:
            self.server_sock.close()


processor = TimeSeriesDataProcessor(window_size=5)
listener = BluetoothListener(
    uuid="00001101-0000-1000-8000-00805F9B34FB",
    service_name="AIEYEAID",
    processor=processor,
)
listener.start_server()
