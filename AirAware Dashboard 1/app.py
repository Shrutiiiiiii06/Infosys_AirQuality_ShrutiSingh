from flask import Flask, render_template, jsonify, request
from data_handler import get_dashboard_data, get_available_cities, load_and_preprocess_data
from flask_cors import CORS 
import numpy as np
import math
import json
from flask import Response

app = Flask(__name__)
CORS(app) 

# Ensure data is loaded when Flask starts
load_and_preprocess_data()

def sanitize_for_json(obj):
    """Recursively convert NaN and Infinity values to None."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    else:
        return obj


@app.route('/')
def dashboard():
    """Renders the main dashboard HTML page, passing the list of cities."""
    # This calls the function to get the list of all available cities
    available_cities = get_available_cities() 
    # Pass the list of cities to the index.html template
    return render_template('index.html', cities=available_cities) 

@app.route('/api/data', methods=['GET'])
def get_data():
    """API endpoint to deliver processed data to the frontend."""
    
    # --- Fix: Get the list of cities here to define the default location ---
    all_cities = get_available_cities()
    default_city = all_cities[0] if all_cities else None

    # Get 'location' from request args, defaulting to the first available city
    location = request.args.get('location', default_city)
    time_range = request.args.get('time_range', 'Last 24 Hours')
    pollutant = request.args.get('pollutant', 'PM2.5')
    
    # Check if a valid city was found before trying to process data
    if not location:
        return jsonify({'error': 'No data or cities available to process.'}), 500
        
    data = get_dashboard_data(city=location, time_range=time_range, pollutant=pollutant)
    
    if data and 'error' not in data:
        clean_data = sanitize_for_json(data)
        return Response(json.dumps(clean_data), mimetype='application/json')
    else:
        return jsonify({'error': 'Could not retrieve data or file is missing.'}), 500
if __name__ == '__main__':
    app.run(debug=True)