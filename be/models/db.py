from config import MONGO_URI
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Dict, List, Optional
from .place import Place
from .review import Review

class MongoDB:
    def __init__(self, uri: str = MONGO_URI):
        try:
            self.client = MongoClient(uri)
            # Test the connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
            
            self.db = self.client['places_db']
            self.places: Collection = self.db['places']
            self.reviews: Collection = self.db['reviews']
            
            # Create indexes
            self.places.create_index("place_id", unique=True)
            self.reviews.create_index([("place_id", 1), ("review_id", 1)], unique=True)
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    def insert_place(self, place: Place) -> str:
        try:
            place_dict = place.dict()
            print("\nInserting place into MongoDB:")
            print("1. Place data:", place_dict)
            
            # Remove _id if it exists
            place_dict.pop('_id', None)
            
            result = self.places.update_one(
                {"place_id": place.place_id},
                {"$set": place_dict},
                upsert=True
            )
            
            print("2. Update result:", {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": result.upserted_id
            })
            
            # Verify the document was stored
            stored_doc = self.places.find_one({"place_id": place.place_id})
            print("3. Stored document:", stored_doc)
            
            return str(result.upserted_id) if result.upserted_id else place.place_id
        except Exception as e:
            print(f"Error inserting into MongoDB: {str(e)}")
            raise

    def insert_review(self, review: Review) -> str:
        review_dict = review.dict()
        result = self.reviews.update_one(
            {
                "place_id": review.place_id,
                "review_id": review.review_id
            },
            {"$set": review_dict},
            upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else review.review_id

    def get_places(self, query: Dict = None) -> List[Place]:
        try:
            query = query or {}
            # Print the MongoDB connection status
            print("MongoDB Connection Status:", self.client.server_info())
            
            all_docs = list(self.places.find({}))
            print("All documents in collection:", all_docs)
            
            cursor = self.places.find(query)
            places = list(cursor)
            print(f"Found {len(places)} documents in MongoDB")
            if places:
                print("Sample document:", places[0])
            else:
                print("No documents found in MongoDB")
            
            return [Place(**place) for place in places]
        except Exception as e:
            print(f"Error querying MongoDB: {e}")
            print(f"Full error details: {str(e)}")
            return []

    def get_reviews(self, place_id: str) -> List[Review]:
        return [Review(**review) for review in self.reviews.find({"place_id": place_id})]

    def get_place_by_id(self, place_id: str) -> Optional[Place]:
        """Get a single place by its ID"""
        try:
            doc = self.places.find_one({"place_id": place_id})
            if doc:
                return Place(**doc)
            return None
        except Exception as e:
            print(f"Error getting place by ID: {str(e)}")
            return None

    def update_place_scraped_status(self, place_id: str, scraped: bool = True) -> bool:
        """Update the scraped status of a place"""
        try:
            result = self.places.update_one(
                {"place_id": place_id},
                {"$set": {"scraped": scraped}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating place scraped status: {str(e)}")
            return False

    def get_all_reviews(self) -> List[Review]:
        """Get all reviews from the database"""
        try:
            reviews = list(self.reviews.find({}))
            print(f"Found {len(reviews)} total reviews")
            return [Review(**review) for review in reviews]
        except Exception as e:
            print(f"Error getting all reviews: {str(e)}")
            return []

    def get_unscraped_places(self) -> List[Place]:
        """Get all places that haven't been scraped yet"""
        try:
            places = list(self.places.find({"scraped": False}))
            print(f"Found {len(places)} unscraped places")
            return [Place(**place) for place in places]
        except Exception as e:
            print(f"Error getting unscraped places: {str(e)}")
            return []

    def update_review_status(self, review_id: str, status: str) -> bool:
        try:
            result = self.reviews.update_one(
                {"review_id": review_id},
                {"$set": {"approval_status": status}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating review status: {e}")
            return False

    def update_ai_response(self, review_id: str, percentage: float, feedback: str) -> bool:
        try:
            result = self.reviews.update_one(
                {"review_id": review_id},
                {
                    "$set": {
                        "ai_percentage": percentage,
                        "ai_response": feedback
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating AI response: {e}")
            return False 
        

        