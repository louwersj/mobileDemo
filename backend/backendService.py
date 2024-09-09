from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
import base64
from datetime import datetime

app = Flask(__name__)

# Enable CORS for all domains
CORS(app)

# Configure logging settings
logStdOut = False  # Change to False if you don't want logging to go to stdout
logFileName = 'app.log'

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

@app.route('/sink/roadSensor', methods=['POST'])
def handleRoadSensor():
    if request.is_json:
        try:
            data = request.get_json()  # Retrieve the JSON data
            timestamp = data.get('timestamp', datetime.now().isoformat())  # Use timestamp from JSON or current time
            logging.info("Received JSON data: %s", data)

            # Save JSON data with timestamp as the filename
            jsonFileName = os.path.join(dataDir, f"{timestamp}.json")
            try:
                with open(jsonFileName, 'w') as jsonFile:
                    json.dump(data, jsonFile, indent=4)
                logging.info("JSON data saved to %s", jsonFileName)
            except IOError as e:
                logging.error(f"Failed to write JSON data to {jsonFileName}: {e}")
                return jsonify({"message": "Failed to write data to file"}), 500

            # Decode and save image if available in the JSON data
            if 'image' in data and data['image']:
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
        app.run(host='0.0.0.0', port=80, debug=True)
    except Exception as e:
        logging.error(f"Error starting Flask application: {e}")
