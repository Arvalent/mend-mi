from serpapi import GoogleSearch
from .api_key import get_api_key_serpapi


def get_location_local_results(q):
  params = {
    "engine": "google_maps",
    "q": q,
    "ll": "@40.7455096,-74.0083012,15.1z",
    "type": "search",
    "api_key": get_api_key_serpapi()
  }

  search = GoogleSearch(params)
  results = search.get_dict()
  coordinates = []
  if results.get("local_results", None):
    local_results = results["local_results"]
    coordinates = [[result["gps_coordinates"]["longitude"],result["gps_coordinates"]["latitude"]] for result in local_results]

  return coordinates

if __name__ == "__main__":
  query = "boat sailing in harbor, Switzerland"
  test = get_location_local_results(query)




