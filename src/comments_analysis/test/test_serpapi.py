from serpapi import GoogleSearch
from api_google_key import get_api_key_serpapi


def extract_comments_google(query, n_comments, save=False, update=False):

    reviews = []

    params = {
      "engine": "google_maps",
      "q": query,
      "type": "search",
      "api_key": get_api_key_serpapi()
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    data_id = results['place_results']["data_id"]

    params = {
      "engine": "google_maps_reviews",
      "data_id": data_id,
      "api_key": get_api_key_serpapi(),
      "hl": 'en'
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    reviews.extend(results["reviews"])
    for i in range(int(n_comments / 10.0)):
      if results['serpapi_pagination']['next_page_token']:
        params.update({"next_page_token": results['serpapi_pagination']['next_page_token']})
        search = GoogleSearch(params)
        results = search.get_dict()
        reviews.extend(results['reviews'])
        for review in results['reviews']:
          print(review['snippet'])
        print()


if __name__ == '__main__':
  extract_comments_google('molino fribourg', 500)
