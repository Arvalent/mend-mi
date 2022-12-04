import asyncio
import json
import math
import random
import re
import string
from typing import List, TypedDict
from urllib.parse import urljoin

from scrapfly import ScrapeApiResponse, ScrapeConfig, ScrapflyClient


async def search_location(query: str, session: ScrapflyClient):
    """
    search for location data from given query.
    e.g. "New York" will return us TripAdvisor's location details for this query
    """
    print(f"searching: {query}")
    url = "https://www.tripadvisor.com/data/graphql/ids"
    payload = json.dumps(
        [
            {
                # Every graphql query has a query ID, in this case it's:
                "query": "c9d791589f937ec371723f236edc7c6b",
                "variables": {
                    "request": {
                        "query": query,
                        "limit": 10,
                        "scope": "WORLDWIDE",
                        "locale": "en-US",
                        "scopeGeoId": 1,
                        "searchCenter": None,
                        # we can define search result types, in this case we want to search locations
                        "types": [
                            "LOCATION",
                            #   "QUERY_SUGGESTION",
                            #   "USER_PROFILE",
                            #   "RESCUE_RESULT"
                        ],
                        # we can further narrow down locations to
                        "locationTypes": [
                            "GEO",
                            "AIRPORT",
                            "ACCOMMODATION",
                            "ATTRACTION",
                            "ATTRACTION_PRODUCT",
                            "EATERY",
                            "NEIGHBORHOOD",
                            "AIRLINE",
                            "SHOPPING",
                            "UNIVERSITY",
                            "GENERAL_HOSPITAL",
                            "PORT",
                            "FERRY",
                            "CORPORATION",
                            "VACATION_RENTAL",
                            "SHIP",
                            "CRUISE_LINE",
                            "CAR_RENTAL_OFFICE",
                        ],
                        "userId": None,
                        "articleCategories": ["default", "love_your_local", "insurance_lander"],
                        "enabledFeatures": ["typeahead-q"],
                    }
                },
            }
        ]
    )

    headers = {
        # we need to generate a random request ID for this request to succeed
        "content-type": "application/json",
        "x-requested-by": "".join(random.choice(string.ascii_lowercase + string.digits) for i in range(64)),
    }
    result = await session.async_scrape(
        ScrapeConfig(
            url=url,
            country="US",
            headers=headers,
            body=payload,
            method="POST",
            asp=True,
        )
    )
    data = json.loads(result.content)
    # return first result
    print(f'found {len(data[0]["data"]["Typeahead_autocomplete"]["results"])} results, taking first one')
    return data[0]["data"]["Typeahead_autocomplete"]["results"][0]["details"]


class Preview(TypedDict):
    id: str
    url: str
    name: str


def parse_search_page(result: ScrapeApiResponse) -> List[Preview]:
    """parsed results from TripAdvisor search page"""
    parsed = []
    # we go through each result box and extract id, url and name:
    for result_box in result.selector.css("div.listing_title>a"):
        parsed.append(
            {
                "id": result_box.xpath("@id").get("").split("_")[-1],
                "url": result_box.xpath("@href").get(""),
                "name": result_box.xpath("text()").get("").split(". ")[-1],
            }
        )
    return parsed


async def scrape_search(query: str, session: ScrapflyClient) -> List[Preview]:
    """Scrape all search results of a search query"""
    # scrape first page
    print(f"{query}: scraping first search results page")
    hotel_search_url = "https://www.tripadvisor.com/" + (await search_location(query, session))["HOTELS_URL"]
    print(f"found hotel search url: {hotel_search_url}")
    first_page = await session.async_scrape(ScrapeConfig(url=hotel_search_url))

    # extract paging meta information from the first page: How many pages there are?
    total_results = int(
        first_page.selector.xpath("//div[@data-main-list-match-count]/@data-main-list-match-count").get()
    )
    next_page_url = first_page.selector.css('a[data-page-number="2"]::attr(href)').get()
    page_size = int(first_page.selector.css('a[data-page-number="2"]::attr(data-offset)').get())
    total_pages = int(math.ceil(total_results / page_size))

    # scrape remaining pages
    print(f"{query}: found total {total_results} results, {page_size} results per page ({total_pages} pages)")
    other_page_urls = [
        # note "oa" stands for "offset anchors"
        urljoin(first_page.context["url"], next_page_url.replace(f"oa{page_size}", f"oa{page_size * i}"))
        for i in range(2, total_pages + 1)
    ]
    # we use assert to ensure that we don't accidentally produce duplicates which means something went wrong
    assert len(set(other_page_urls)) == len(other_page_urls)

    results = parse_search_page(first_page)
    async for result in session.concurrent_scrape([ScrapeConfig(url=url, country="US") for url in other_page_urls]):
        results.extend(parse_search_page(result))
    return results


def extract_page_manifest(html):
    """extract javascript state data hidden in TripAdvisor HTML pages"""
    data = re.findall(r"pageManifest:({.+?})};", html, re.DOTALL)[0]
    return json.loads(data)


def extract_named_urql_cache(urql_cache: dict, pattern: str):
    """extract named urql response cache from hidden javascript state data"""
    data = json.loads(next(v["data"] for k, v in urql_cache.items() if pattern in v["data"]))
    return data


class Review(TypedDict):
    id: str
    date: str
    rating: str
    title: str
    text: str
    votes: int
    url: str
    language: str
    platform: str
    author_id: str
    author_name: str
    author_username: str


def parse_reviews(result: ScrapeApiResponse) -> Review:
    """Parse reviews from a review page"""
    page_data = extract_page_manifest(result.content)
    review_cache = extract_named_urql_cache(page_data["urqlCache"], '"reviewListPage"')
    parsed = []
    # review data contains loads of information, let's parse only the basic in this tutorial
    for review in review_cache["locations"][0]["reviewListPage"]["reviews"]:
        parsed.append(
            {
                "id": review["id"],
                "date": review["publishedDate"],
                "rating": review["rating"],
                "title": review["title"],
                "text": review["text"],
                "votes": review["helpfulVotes"],
                "url": review["route"]["url"],
                "language": review["language"],
                "platform": review["publishPlatform"],
                "author_id": review["userProfile"]["id"],
                "author_name": review["userProfile"]["displayName"],
                "author_username": review["userProfile"]["username"],
            }
        )
    return parsed


class Hotel(TypedDict):
    name: str
    id: str
    type: str
    description: str
    rating: float
    rating_count: int
    features: List[str]
    stars: int


def parse_hotel_info(data: dict) -> Hotel:
    """parse hotel data from TripAdvisor javascript state to something more readable"""
    parsed = {}
    # there's a lot of information in hotel data, in this tutorial let's extract the basics:
    parsed["name"] = data["name"]
    parsed["id"] = data["locationId"]
    parsed["type"] = data["accommodationType"]
    parsed["description"] = data["locationDescription"]
    parsed["rating"] = data["reviewSummary"]["rating"]
    parsed["rating_count"] = data["reviewSummary"]["count"]
    # for hotel "features" lets just extract the names:
    parsed["features"] = []
    for amenity_type, values in data["detail"]["hotelAmenities"]["highlightedAmenities"].items():
        for value in values:
            parsed["features"].append(f"{amenity_type}_{value['amenityNameLocalized'].lower()}")

    if star_rating := data["detail"]["starRating"]:
        parsed["stars"] = star_rating[0]["tagNameLocalized"]
    return parsed


class HotelAllData(TypedDict):
    info: Hotel
    reviews: List[Review]
    price: dict


async def scrape_hotel(url: str, session: ScrapflyClient) -> HotelAllData:
    """Scrape all hotel data: information, pricing and reviews"""
    first_page = await session.async_scrape(ScrapeConfig(url=url, country="US"))
    page_data = extract_page_manifest(first_page.content)

    # price data keys are dynamic first we need to find the full key name
    _pricing_key = next(
        (key for key in page_data["redux"]["api"]["responses"] if "/hotelDetail" in key and "/heatMap" in key)
    )
    pricing_details = page_data["redux"]["api"]["responses"][_pricing_key]["data"]["items"]

    # We can extract data from Graphql cache embeded in the page
    # TripAdvisor is using: https://github.com/FormidableLabs/urql as their graphql client
    hotel_cache = extract_named_urql_cache(page_data["urqlCache"], '"locationDescription"')
    hotel_info = hotel_cache["locations"][0]

    # for reviews we first need to scrape multiple pages
    # so, first let's find total amount of pages
    total_reviews = hotel_info["reviewSummary"]["count"]
    _review_page_size = 10
    total_review_pages = int(math.ceil(total_reviews / _review_page_size))
    # then we can scrape all review pages concurrently
    # note: in review url "or" stands for "offset reviews"
    review_urls = [
        url.replace("-Reviews-", f"-Reviews-or{_review_page_size * i}-") for i in range(2, total_review_pages + 1)
    ]
    assert len(set(review_urls)) == len(review_urls)
    reviews = parse_reviews(first_page)
    async for result in session.concurrent_scrape([ScrapeConfig(url=url, country="US") for url in review_urls]):
        reviews.extend(parse_reviews(result))

    return {
        "price": pricing_details,
        "info": parse_hotel_info(hotel_info),
        "reviews": reviews,
    }


async def run():
    with ScrapflyClient(key="YOUR_SCRAPFLY_KEY", max_concurrency=2) as session:
        #result_location = await search_location("Malta", session=session)
        #result_search = await scrape_search("Malta", session)
        result_hotel = await scrape_hotel(
            "https://www.tripadvisor.com/Hotel_Review-g190327-d264936-Reviews-1926_Hotel_Spa-Sliema_Island_of_Malta.html",
            session,
        )


if __name__ == "__main__":
    asyncio.run(run())