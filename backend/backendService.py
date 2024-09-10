from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
import base64
from datetime import datetime
import requests
import time

app = Flask(__name__)

# Enable CORS for all domains
CORS(app)

# Configure logging settings
logStdOut = False  # Change to True if you want logging to go to stdout
logFileName = 'app.log'

# New variables to control local storage
storeDataLocal = False   # Set to False to disable storing JSON files locally
storeImageLocal = False  # Set to False to disable storing and decoding images

# Setup logging to both file and stdout if logStdOut is True
if logStdOut:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(logFileName),
                            logging.StreamHandler()
                        ])
else:
    logging.basicConfig(filename=logFileName, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

# Directory and file paths
dataDir = './data'
imageDir = './images'

# Ensure data and image directories exist
for directory in [dataDir, imageDir]:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logging.info(f"Directory {directory} created successfully.")
        except Exception as e:
            logging.error(f"Failed to create directory {directory}: {e}")

def storeRoadSensorData(data):
    try:
        # Convert ISO timestamp to EPOCH timestamp
        timestamp_iso = data.get('timestamp')
        if timestamp_iso:
            timestamp_epoch = int(time.mktime(datetime.strptime(timestamp_iso, '%Y-%m-%dT%H:%M:%S.%fZ').timetuple()))
        else:
            raise ValueError("No timestamp provided in data")

        # Extract required values from data
        orientation_alpha = data.get('orientation', {}).get('alpha')
        orientation_beta = data.get('orientation', {}).get('beta')
        orientation_gamma = data.get('orientation', {}).get('gamma')

        acceleration_x = data.get('motion', {}).get('acceleration', {}).get('x')
        acceleration_y = data.get('motion', {}).get('acceleration', {}).get('y')
        acceleration_z = data.get('motion', {}).get('acceleration', {}).get('z')

        location_lat = data.get('gps', {}).get('latitude')
        location_lon = data.get('gps', {}).get('longitude')
        location_acc = data.get('gps', {}).get('accuracy')

        image = data.get('image')

        # Prepare the payload for the POST request
        payload = {
            "timestamp": timestamp_epoch,
            "orientation_alpha": orientation_alpha,
            "orientation_beta": orientation_beta,
            "orientation_gamma": orientation_gamma,
            "acceleration_x": acceleration_x,
            "acceleration_y": acceleration_y,
            "acceleration_z": acceleration_z,
            "location_lat": location_lat,
            "location_lon": location_lon,
            "location_acc": location_acc,
            "image": image
        }

        # URL for the API endpoint
        url = 'https://idhqf8a2uwbse4v-kiwa.adb.eu-frankfurt-1.oraclecloudapps.com/ords/admin/roadtable/'

        # Print the full payload if logStdOut is set to True
        if logStdOut:
            print("Payload:", payload)

        # Execute the POST request
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=payload, headers=headers)

        # Log and print the result of the POST request
        if response.status_code == 201:
            logging.info(f"Data sent successfully: {response.text}")
            print("Curl command successful: Data sent successfully.")
        else:
            logging.error(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")
            print(f"Curl command failed. Status code: {response.status_code}")

    except Exception as e:
        logging.error(f"Error in storeRoadSensorData: {e}")
        print(f"Error in storeRoadSensorData: {e}")

@app.route('/sink/roadSensor', methods=['POST'])
def handleRoadSensor():
    if request.is_json:
        try:
            data = request.get_json()  # Retrieve the JSON data
            timestamp = data.get('timestamp', datetime.now().isoformat())  # Use timestamp from JSON or current time
            logging.info("Received JSON data: %s", data)

            # Store JSON data locally if storeDataLocal is True
            if storeDataLocal:
                jsonFileName = os.path.join(dataDir, f"{timestamp}.json")
                try:
                    with open(jsonFileName, 'w') as jsonFile:
                        json.dump(data, jsonFile, indent=4)
                    logging.info("JSON data saved to %s", jsonFileName)
                except IOError as e:
                    logging.error(f"Failed to write JSON data to {jsonFileName}: {e}")
                    return jsonify({"message": "Failed to write data to file"}), 500

            # Send the data to storeRoadSensorData for further processing
            storeRoadSensorData(data)

            # Decode and save image if available and storeImageLocal is True
            if storeImageLocal and 'image' in data and data['image']:
                try:
                    imageFileName = os.path.join(imageDir, f"{timestamp}.png")
                    imageData = base64.b64decode(data['image'])
                    with open(imageFileName, 'wb') as imageFile:
                        imageFile.write(imageData)
                    logging.info("Image saved to %s", imageFileName)
                except Exception as e:
                    logging.error(f"Failed to save image: {e}")
                    return jsonify({"message": "Failed to save image"}), 500

            return jsonify({"message": "received"}), 200
        except Exception as e:
            logging.error(f"Error processing JSON data: {e}")
            return jsonify({"message": "Error processing data"}), 500
    else:
        logging.warning("Invalid request. JSON data expected.")
        return jsonify({"message": "Invalid request. JSON data expected."}), 400

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=80, debug=False)
    except Exception as e:
        logging.error(f"Error starting Flask application: {e}")
