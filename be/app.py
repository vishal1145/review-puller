from flask import Flask, jsonify, request
from models.db import MongoDB
from models.place import Place
from models.review import Review, Reviewer
from datetime import datetime
import requests
from config import GOOGLE_MAPS_API_KEY, MONGO_URI
from google_place_scrapper import get_google_review_by_place_id
from scrapper import get_city_coordinates

app = Flask(__name__)

try:
    db = MongoDB(MONGO_URI)
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit(1)

def fetch_and_store_places(latitude: float, longitude: float, place_type: str = "restaurant", radius: int = 1500):
    API_URL = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={place_type}&key={GOOGLE_MAPS_API_KEY}"
    
    print(f"\n1. Calling Google API: {API_URL}")
    response = requests.get(API_URL)
    print(f"2. API Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        places = data.get("results", [])
        print(f"3. Number of places received from API: {len(places)}")
        
        if not places:
            print("No places received from Google API")
            return []

        stored_places = []
        for place_data in places:
            try:
                print(f"\n4. Processing place: {place_data.get('name')}")
                place = Place(
                    place_id=place_data["place_id"],
                    name=place_data["name"],
                    address=place_data.get("vicinity"),
                    latitude=place_data["geometry"]["location"]["lat"],
                    longitude=place_data["geometry"]["location"]["lng"],
                    rating=place_data.get("rating"),
                    total_ratings=place_data.get("user_ratings_total"),
                    scraped=False
                )
                
                print("5. Created Place object:", place.dict())
                result = db.insert_place(place)
                print(f"6. MongoDB insert result: {result}")
                
                stored_places.append(place.dict())
                print(f"7. Added to stored_places list. Current count: {len(stored_places)}")
                
            except Exception as e:
                print(f"Error processing place: {str(e)}")
                continue
        
        print(f"\n8. Total places stored: {len(stored_places)}")
        return stored_places
    else:
        print(f"API Error: {response.status_code}")
        print(f"API Response: {response.text}")
        return []

@app.route('/fetch_places', methods=['GET'])
def fetch_places():
    city = request.args.get('city')
    place_type = request.args.get('type')
    radius = int(request.args.get('radius'))
    
    print(f"Fetching {place_type}s in {city} within {radius}m radius")
    
    try:
        coordinates = get_city_coordinates(city)
        print(f"Coordinates for {city}: {coordinates}")
        
        if not coordinates:
            return jsonify({
                "error": f"Could not find coordinates for city: {city}"
            }), 400
            
        latitude, longitude = coordinates
        
        places = fetch_and_store_places(latitude, longitude, place_type, radius)
        print(f"Found {len(places)} places in {city}")
        
        response_data = {
            "city": city,
            "coordinates": {"lat": latitude, "lng": longitude},
            "type": place_type,
            "radius": radius,
            "places_count": len(places),
            "places": places
        }
        
        print(f"Sending response with {len(places)} places")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in fetch_places: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/get_places', methods=['GET'])
def get_places():
    try:
        places = db.get_places()
        print(f"Retrieved {len(places)} places from MongoDB")
        result = [place.dict() for place in places]
        print(f"Converted places to dict: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Error getting places: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/fetch_reviews', methods=['GET'])
def fetch_reviews():
    try:
        print("\nEndpoint /fetch_reviews hit!")  # Check if the endpoint is accessed

        print("Fetching unscraped places...")
        places = db.get_unscraped_places()

        if places is None:
            print("Error: get_unscraped_places() returned None")
            return jsonify({"error": "Database query failed"}), 500
        
        print(f"1. Found {len(places)} unscraped places")
        
        all_stored_reviews = []
        
        for place in places:
            try:
                print(f"\n2. Fetching reviews for place: {place.name} ({place.place_id})")
                
                reviews = get_google_review_by_place_id(place.place_id)
                if reviews is None:
                    print(f"Error: get_google_review_by_place_id() returned None for {place.name}")
                    continue
                
                print(f"3. Found {len(reviews)} reviews")

                place_reviews = []
                for review_data in reviews:
                    try:
                        review = Review(
                            review_id=review_data["review_id"],
                            place_id=place.place_id,
                            place_name = place.name,
                            reviewer=Reviewer(
                                display_name=review_data["reviewer"]["display_name"],
                                profile_photo_url="",
                                link=""
                            ),
                            link="",
                            source="Google",
                            source_logo="https://www.gstatic.com/images/branding/product/1x/googleg_48dp.png",
                            rating="0/5",
                            created="",
                            date="",
                            comment=review_data.get("comment", ""),
                            photos=[],
                            checked=False,
                        )
                        
                        result = db.insert_review(review)
                        print(f"4. Stored review {result}")
                        place_reviews.append(review.dict())
                        
                    except Exception as e:
                        print(f"Error processing review: {str(e)}")
                        continue

                db.update_place_scraped_status(place.place_id, True)
                print(f"5. Marked place {place.name} as scraped")

                all_stored_reviews.append({
                    "place_id": place.place_id,
                    "place_name": place.name,
                    "reviews_count": len(place_reviews),
                    "reviews": place_reviews
                })
                
            except Exception as e:
                print(f"Error processing place {place.place_id}: {str(e)}")
                continue

        print("Finalizing response...")
        response_data = {
            "places_processed": len(places),
            "total_reviews": sum(p["reviews_count"] for p in all_stored_reviews),
            "results": all_stored_reviews
        }
        print("Response data prepared successfully")

        return jsonify(response_data)

    except Exception as e:
        print(f"Error fetching reviews: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/fetch_reviews/<place_id>', methods=['GET'])
def fetch_reviews_by_id(place_id):
    try:
        place = db.get_place_by_id(place_id)
        if not place:
            return jsonify({
                "error": f"Place with ID {place_id} not found"
            }), 404
            
        print(f"\n1. Fetching reviews for place: {place.name} ({place_id})")
        
        reviews = get_google_review_by_place_id(place_id)
        print(f"2. Found {len(reviews)} reviews")
        
        stored_reviews = []
        for review_data in reviews:
            try:
                review = Review(
                    review_id=review_data["review_id"],
                    place_id=place_id,
                    reviewer=Reviewer(
                        display_name=review_data["reviewer"]["display_name"],
                        profile_photo_url="",
                        link=""
                    ),
                    link="",
                    source="Google",
                    source_logo="https://www.gstatic.com/images/branding/product/1x/googleg_48dp.png",
                    rating="0/5",
                    created="",
                    date="",
                    comment=review_data.get("comment", ""),
                    photos=[],
                    checked=False
                )
                
                result = db.insert_review(review)
                print(f"3. Stored review {result}")
                stored_reviews.append(review.dict())
                
            except Exception as e:
                print(f"Error processing review: {str(e)}")
                continue
        
        db.update_place_scraped_status(place_id, True)
        print(f"4. Marked place as scraped")
        
        return jsonify({
            "place_id": place_id,
            "place_name": place.name,
            "reviews_count": len(stored_reviews),
            "reviews": stored_reviews
        })
        
    except Exception as e:
        print(f"Error fetching reviews: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/list_places', methods=['GET'])
def list_places():
    try:
        places = db.get_places()
        return jsonify([{
            "place_id": place.place_id,
            "name": place.name,
            "address": place.address
        } for place in places])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list_ureviews', methods=['GET'])
def list_reviews():
    try:
        place_id = request.args.get('place_id')
        
        if place_id:
            reviews = db.get_reviews(place_id)
        else:
            reviews = db.get_all_reviews()
            
        return jsonify({
            "count": len(reviews),
            "reviews": [review.dict() for review in reviews]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5999,debug=True)
