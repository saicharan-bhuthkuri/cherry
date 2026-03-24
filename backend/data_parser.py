import re
import pandas as pd

def parse_accident_data(filepath):
    records = []
    # Columns expected: year, mandal, accident_prone_area, latitude, longitude, road_type, vehicles, fatalities, injuries, accident_type, weather, cause
    # We can use regex to extract the structured parts
    # Pattern: ^(\d{4})\s+([\w]+)\s+(.+?)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(junction|urban\s+road|highway|rural\s+road)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+?)\s+(clear|foggy|cloudy|rainy)\s+(.+)$
    
    # A cleaner approach is locating lat/lon (two floats adjacent), and numbers for veh/fat/inj
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines[1:]: # Skip header
        line = line.strip()
        if not line:
            continue
            
        # Find the two floats
        float_matches = list(re.finditer(r'\b\d{2}\.\d+\s+\d{2}\.\d+\b', line))
        if not float_matches:
            continue
        
        floats_str = float_matches[0].group()
        lat_str, lon_str = floats_str.split()
        
        lat_idx = float_matches[0].start()
        lon_end_idx = float_matches[0].end()
        
        # Left of floats: year mandal area
        left_part = line[:lat_idx].strip()
        left_tokens = left_part.split(' ', 2)
        year = int(left_tokens[0])
        mandal = left_tokens[1]
        area = left_tokens[2] if len(left_tokens) > 2 else ""
        
        # Right of floats: road_type vehicles fatalities injuries accident_type weather cause
        right_part = line[lon_end_idx:].strip()
        
        # Find the 3 consecutive integers for veh, fat, inj
        ints_match = re.search(r'\b(\d+)\s+(\d+)\s+(\d+)\b', right_part)
        if not ints_match:
            continue
            
        road_type = right_part[:ints_match.start()].strip()
        vehicles = int(ints_match.group(1))
        fatalities = int(ints_match.group(2))
        injuries = int(ints_match.group(3))
        
        # Rest: accident_type, weather, cause
        rest_part = right_part[ints_match.end():].strip()
        
        # Weather is one of: clear, foggy, cloudy, rainy. We can find it to split.
        weather_match = re.search(r'\b(clear|foggy|cloudy|rainy)\b', rest_part, re.IGNORECASE)
        if weather_match:
            acc_type = rest_part[:weather_match.start()].strip()
            weather = weather_match.group(1)
            cause = rest_part[weather_match.end():].strip()
        else:
            acc_type = rest_part
            weather = "unknown"
            cause = "unknown"
            
        records.append({
            'year': year, 'mandal': mandal, 'accident_prone_area': area,
            'latitude': float(lat_str), 'longitude': float(lon_str),
            'road_type': road_type, 'vehicles': vehicles,
            'fatalities': fatalities, 'injuries': injuries,
            'accident_type': acc_type, 'weather': weather, 'cause': cause
        })
        
    return pd.DataFrame(records)
