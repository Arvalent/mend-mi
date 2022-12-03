"""
Description: this file defines method that can be used to extract comments from different platform for a specific topic

Platform:
    - Google: location and comments about these location
    - TripAdvisor: restaurants name or url link and find object


"""
import json
import googlemaps
import os

from api_google_key import get_api_key


def extract_comments(place_id, api_key, update=False, save=False, output_path=None):

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


if __name__ == "__main__":

    data_path = r"C:\Users\Lucas\Desktop\Lauzhack2022\mend-mi\data"
    API_KEY = get_api_key()

    test_id = "ChIJz1bX4zMujEcRDLSYjd7SNyk"
    test = extract_comments(test_id, API_KEY, save=True, output_path=data_path)

