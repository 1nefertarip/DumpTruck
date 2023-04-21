# !pip install geopandas
import geopandas as gpd
from shapely.geometry import LineString
import requests
import json
import time
from datetime import datetime, timezone, timedelta

# Set your HERE Maps API credentials
app_code = 'YOUR API KEY'

def output_gpd(result):
    # Create a list to store the polyline data
    polyline_data = []

    # Loop through each location in the result
    for location in result['results'][0:]:
        # Loop through each link in the location and add the polyline data to the list
        for link in location['location']['shape']['links']:
            points = [(point['lng'], point['lat']) for point in link['points']]
            jamFactor = location['currentFlow']['jamFactor']
            # description = location['location']['description']
            # speed = location['currentFlow']['speed']
            # speedUncapped = location['currentFlow']['speedUncapped']
            # freeFlow = location['currentFlow']['freeFlow']
            polyline_data.append({
                'geometry': LineString(points),
                # 'description': description,
                'jamFactor': jamFactor,
                # 'speed': speed,
                # 'speedUncapped': speedUncapped,
                # 'freeFlow': freeFlow
                }
            )

    # Create a GeoDataFrame from the polyline data and specify the CRS
    df = gpd.GeoDataFrame(polyline_data)

    return df

# Define the bbox parameters
# This is the whole NL
west_longitude_min = 3.3079377
south_latitude_min = 50.7503674
east_longitude_max = 7.22749845
north_latitude_max = 53.5764232
bbox_width = 1 # max value per call
bbox_height = 1

# Initialize a list to store the results
results = []

# Initialize time
amsterdam_tz = timezone(timedelta(hours=1))
now = datetime.now(amsterdam_tz)
current_time = now.strftime(f"%Y-%m-%d_%H%M")

# Loop through the bboxes
for i in range(int((east_longitude_max - west_longitude_min) // bbox_width)+1):
    for j in range(int((north_latitude_max - south_latitude_min) // bbox_height)+1):
        # Calculate the bbox coordinates
        west_longitude = west_longitude_min + i * bbox_width
        south_latitude = south_latitude_min + j * bbox_height
        east_longitude = west_longitude + bbox_width
        north_latitude = south_latitude + bbox_height
        
        # Set the API endpoint URL
        url = f'https://data.traffic.hereapi.com/v7/flow?in=bbox:{west_longitude},{south_latitude},{east_longitude},{north_latitude}&locationReferencing=shape&apiKey={app_code}'

        # Make the API request
        response = requests.get(url)

        # Check if the request is successful
        if response.status_code == 200:
            # Convert the response to JSON format and output a GeoDataFrame
            result = json.loads(response.content.decode('utf-8'))
            df = output_gpd(result)
            # Check if the GeoDataFrame has a 'geometry' column
            if 'geometry' in df.columns:
                # Add CRS
                df.crs = 'EPSG:4326'
                # Write the GeoDataFrame to a GeoPackage file with a specified CRS
                df.to_file(f'output{i}-{j}_{current_time}.gpkg', driver='GPKG')
            else:
                print(f'Skipping bbox {i+1},{j+1} - no geometry field found')
        else:
            print(f'Request for bbox {i+1},{j+1} failed with status code {response.status_code}')
        time.sleep(0.5)

# Print the results
print(results)