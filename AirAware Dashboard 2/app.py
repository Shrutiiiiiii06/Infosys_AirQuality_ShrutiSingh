import pandas as pd
from flask import Flask, render_template, jsonify, request
from data_handler import get_dashboard_data, get_available_cities 
from flask_cors import CORS 

app = Flask(__name__)
CORS(app) 

@app.route('/')
def dashboard():
    """Renders the main dashboard HTML page, passing the list of cities."""
    # This call is needed to ensure the data handler runs and loads the data early.
    available_cities = get_available_cities() 
    return render_template('index.html', cities=available_cities) 

@app.route('/api/data', methods=['GET'])
def get_data():
    """API endpoint to deliver processed data to the frontend."""
    
    # 🌟 FIX 1: Safely determine the default city from the loaded data
    all_cities = get_available_cities()
    
    # If cities exist, use the request parameter (if present and not empty) 
    # or default to the first city. If no cities, default to None.
    default_city = all_cities[0] if all_cities else None
    
    # FIX 2: Explicitly check for an empty location string from the frontend.
    # Since location is REMOVED from the HTML, location_param will be an empty string or None.
    # We MUST default to the first city retrieved from the data handler.
    location_param = request.args.get('location')

    # If the param is not provided (or is an empty string 'null'), use the safe default.
    # This prevents the critical 500 error.
    location = default_city
    
    time_range = request.args.get('time_range', 'Last 24 Hours')
    pollutant = request.args.get('pollutant', 'PM2.5')
    
    # Check if a valid city was found before trying to process data
    if not location:
        # This occurs if get_available_cities() returns an empty list (data loading failed)
        return jsonify({'error': 'FATAL: Data file contains no records or is unreadable. Could not determine default city.'}), 500
        
    data = get_dashboard_data(city=location, time_range=time_range, pollutant=pollutant)
    
    if data and 'error' not in data:
        return jsonify(data)
    else:
        # This handles crashes originating within get_dashboard_data
        return jsonify({'error': 'Internal Server Error during data processing.'}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)

### Summary of Changes:

# The logic within `get_data()` was simplified to:
# ```python
# location = default_city
