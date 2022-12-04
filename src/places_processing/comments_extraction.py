"""
Description: this file defines method that can be used to extract comments from different platform for a specific topic

Platform:
    - Google: location and comments about these location
    - TripAdvisor: restaurants name or url link and find object


"""
import json
import googlemaps
import os
import re
from serpapi import GoogleSearch

from .api_key import get_api_key, get_api_key_serpapi


def extract_comments_google_maps_api(place_id, api_key, update=False, save=False, output_path=None):

    output_file = os.path.join(output_path, place_id+".json")

    if os.path.exists(output_file) and not update:
        print("Location already exists no API call made")
        print("If you want to update the comments: update=True")

    map_client = googlemaps.Client(api_key)

    response = map_client.place(place_id=place_id)
    comments = response['result']['reviews']
    place_comments = {'comments': {i: comment for i, comment in enumerate(comments)}}

    # TODO: ensure we do not erase previous comments
    if save or update:
        if not output_path:
            print("Could not be saved needs to specify output_path parameter." )
        else:
            with open(os.path.join(output_path, place_id + ".json"), 'w') as outfile:
                json.dump(place_comments, outfile, indent=4)

    return place_comments


def extract_comments_serpapi_api(place_id, n_comments, save=False, output_path=None, update=False):

    API_KEY = get_api_key_serpapi()  # To replace with your API key

    reviews = {'rating': None, 'comments': {}}  # storage

    # Search for the place
    params = {"engine": "google_maps", "data": place_id, "type": "place", "api_key": API_KEY}
    search = GoogleSearch(params)
    results = search.get_dict()
    search_id = results['search_metadata']['id']

    # Check params and if file already exists
    output_file = None
    if save:
        output_file = os.path.join(output_path, search_id+".json")
        if not output_path:
            print('save data but not output path given')
            return {}

        elif os.path.exists(output_file) and not update:
            print("Location already exists no API call made")
            print("If you want to update the comments: update=True")
            return {}

    data_id = results['place_results']["data_id"]
    reviews['data_id'] = data_id
    if results['place_results'].get('rating',None):
        reviews['rating'] = results['place_results']['rating']
    if results['place_results'].get('type', None):
        reviews['type'] = results['place_results']['type']
    if results['place_results'].get('extensions', None):
        reviews['extensions'] = results['place_results']['extensions']
    if results['place_results'].get('title', None):
        reviews['name'] = results['place_results']['title']
    similar_places = None
    if results['place_results'].get('people_also_search_for', None):
        similar_places = results['place_results']['people_also_search_for'][0]['local_results']
    reviews['similar_results'] = {}
    if similar_places:
        for i, similar in enumerate(similar_places):
            reviews['similar_results'].update({similar['data_id']: similar['title']})

    # Extract comment from the place 10 by 10 to do a mood extraction
    params = {"engine": "google_maps_reviews", "data_id": data_id, "api_key": API_KEY,  "hl": 'en'}
    search = GoogleSearch(params)
    results = search.get_dict()
    if results.get("reviews", None):
        reviews['comments'].update({str(int(i)): result['snippet'] for i, result in enumerate(results['reviews'])})
        last_key = int(max(list(reviews['comments'].keys())))
        for i in range(int(n_comments / 10.0)):
            if results['serpapi_pagination']['next_page_token']:
                params.update({"next_page_token": results['serpapi_pagination']['next_page_token']})
                search = GoogleSearch(params)
                results = search.get_dict()
                for j, result in enumerate(results['reviews']):
                    # if the text is translated
                    if 'Translated' in result['snippet']:
                        text = result['snippet']
                        start_ = re.search('Translated by Google\) ', text).end()
                        end_ = re.search(" \(Original\)", text).start()
                        text = text[start_:end_]
                        reviews['comments'].update({str(last_key+j+i*10): text})
                    # plain text
                    else:
                        reviews['comments'].update({str(last_key+j+i*10): result['snippet']})

    # TODO: ensure we do not erase previous comments
    if output_file:
        with open(output_file, 'w') as outfile:
            json.dump(reviews, outfile, indent=4)

    return reviews


def extract_comment_tripadvisor():
    raise NotImplementedError


if __name__ == "__main__":

    data_path = r"/data"
    API_KEY = get_api_key()

    test_id = "ChIJz1bX4zMujEcRDLSYjd7SNyk"

    # Changed to serpapi
    # test = extract_comments_google_maps_api(test_id, API_KEY, save=True, output_path=data_path)

    test_id_serp = "!4m5!3m4!1s0x0:0x3a6ff8042927ea2c!8m2!3d46.8053241!4d7.1562764"  # Restaurant Molino, Fribourg
    test_id_serp = "!4m5!3m4!1s0x0:0x47188bb9f8d68e6b!8m2!3d46.5246408!4d6.6143108" # Evade, Escape Game, Lausanne
    test = extract_comments_serpapi_api(test_id_serp, n_comments=50, save=True, output_path=data_path)
