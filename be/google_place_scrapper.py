# #!/usr/bin/env python
# #!/usr/bin/env python
# print('If you get error "ImportError: No module named \'six\'" install six:\n'+\
#     '$ sudo pip install six');
# print('To enable your free eval account and get CUSTOMER, YOURZONE and ' + \
#     'YOURPASS, please contact sales@brightdata.com')
import sys
import ssl
import json
import re

user_name = 'brd-customer-hl_dde63074-zone-serp_api1'
user_pass = 'og3lsqhf3n5k'
proxy = 'brd.superproxy.io:33335'

def get_google_review_by_place_id(place_id):
    ssl._create_default_https_context = ssl._create_unverified_context
    if sys.version_info[0]==2:
        import six
        from six.moves.urllib import request
        opener = request.build_opener(
            request.ProxyHandler(
                {'http': 'http://'+user_name+':'+user_pass+'@'+proxy,
                'https': 'http://'+user_name+':'+user_pass+'@'+proxy}))
        raw_response = opener.open('https://www.google.com/reviews?fid='+place_id).read().decode("utf-8")
    if sys.version_info[0]==3:
        import urllib.request
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler(
                {'http': 'http://'+user_name+':'+user_pass+'@'+proxy,
                'https': 'http://'+user_name+':'+user_pass+'@'+proxy}))
        raw_response = opener.open('https://www.google.com/reviews?fid='+place_id).read().decode("utf-8")
        
    # with open(f"{place_id}.txt", "w", encoding="utf-8") as f:
    #     f.write(raw_response)
    
    reviews = review_encoder(raw_response)
        
    return reviews
            

def review_encoder(raw_response):
    cleaned_response = re.sub(r"^\)\]\}'\n", "", raw_response)

    try:
        data = json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        exit()

    reviews = []

    if len(data) > 2 and isinstance(data[2], list):
        review_entries = data[2] 

        for review_entry in review_entries:
            try:
                converted_review = convert_google_review(review_entry)
                reviews.append(converted_review)
            except Exception as e:
                print("Skipping an entry due to error:", e)

    # Step 4: Print the Extracted Reviews
    if reviews:
        return reviews
    else:
        return []
 
    
def convert_google_review(raw_data):
    """Convert raw Google review data into a structured format."""
    try:
        # Extract base review data
        review_data = raw_data[0]
        #print(len(review_data[2]))
        
        # for i in range(len(review_data[1][4])):
        #     print(i)
        #     print(review_data[1][4][i])
            
        
        #print(len(review_data))
        reviewer_info = review_data[1][4][5]
        # photo_data = raw_data[0][2][0][0][1]
        
        # Build structured review object
        
        structured_review = {
            "review_id": review_data[0],
            "reviewer": {
                #"profile_photo_url": reviewer_info[1],
                "display_name": reviewer_info[0],
                #"link": reviewer_info[2][0]
            },
            #"link": raw_data[2][7][0][3][0],
            #"source": review_data[1][8][0],
            #"source_logo": review_data[1][8][1],
            #"rating": f"{review_data[1][8][4]}/5",
            # "created": review_data[1][2],
            # "date": f"{review_data[2][0][2][8][0]}-{review_data[2][0][2][8][1]}-{review_data[2][0][2][8][2]}",
            "comment": review_data[2][15][0][0],
            # "photos": [
            #     photo_data[6][0] if photo_data and photo_data[6] else None
            # ]
        }
        
        # Remove None values from photos array
        #structured_review["photos"] = [p for p in structured_review["photos"] if p]
        
        return structured_review
    except Exception as e:
        print(f"Error converting review: {str(e)}")
        return None

    
