from google_place_scrapper import get_google_review_by_place_id, review_encoder
import requests
from typing import List, Dict
import json
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
# Configuration
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY') 
BASE_URL = "https://maps.googleapis.com/maps/api/"

def get_places_in_city(latitude: float, longitude: float, radius: int = 1500, place_type: str = "restaurant") -> List[Dict]:
    """
    Get list of places in a city using Google Places API
    
    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location
        radius (int): Search radius in meters
        place_type (str): Type of place to search for
        
    Returns:
        List[Dict]: List of places with their details
    """
    
    url = f"{BASE_URL}/nearbysearch/json"
    params = {
        "location": f"{latitude},{longitude}",
        "radius": radius,
        "type": place_type,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        results = response.json().get("results", [])
        places = []
        
        for place in results:
            place_data = {
                "place_id": place.get("place_id"),
                "name": place.get("name"),
                "address": place.get("vicinity"),
                "latitude": place["geometry"]["location"]["lat"],
                "longitude": place["geometry"]["location"]["lng"],
                "rating": place.get("rating"),
                "total_ratings": place.get("user_ratings_total"),
                "scraped": 0,  # Flag for tracking if reviews have been scraped
                "created_at": datetime.now().isoformat()
            }
            places.append(place_data)
            
        return places
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching places: {e}")
        return []

def get_place_reviews(place_id: str) -> List[Dict]:
    """
    Get reviews for a specific place using Google Place Scrapper
    
    Args:
        place_id (str): Google Place ID
        
    Returns:
        List[Dict]: List of reviews for the place
    """
    try:
        # Get raw reviews using the existing scrapper function
        raw_reviews = get_google_review_by_place_id(place_id)
        
        # Process the reviews using the existing encoder
        reviews = review_encoder(raw_reviews)
        
        # Add additional metadata to each review
        for review in reviews:
            review.update({
                "place_id": place_id,
                "checked": 0,  # Flag for processing status
                "created_at": datetime.now().isoformat()
            })
            
        return reviews
    
    except Exception as e:
        print(f"Error fetching reviews for place {place_id}: {e}")
        return []

def get_city_coordinates(city_name: str) -> tuple:
    """
    Get latitude and longitude for a city using Google Geocoding API
    
    Args:
        city_name (str): Name of the city
        
    Returns:
        tuple: (latitude, longitude)
    """
    url = f"{BASE_URL}geocode/json"
    params = {
        "address": city_name,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        results = response.json().get("results", [])
        if results:
            location = results[0]["geometry"]["location"]
            return location["lat"], location["lng"]
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting coordinates for {city_name}: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    # Example coordinates for Sydney, Australia
    sydney_lat = -33.8670522
    sydney_lng = 151.1957362
    
    # Get places
    places = get_places_in_city(sydney_lat, sydney_lng)
    print(f"Found {len(places)} places")
    
    # Get reviews for the first place
    if places:
        first_place = places[0]
        reviews = get_place_reviews(first_place["place_id"])
        print(f"Found {len(reviews)} reviews for {first_place['name']}") 