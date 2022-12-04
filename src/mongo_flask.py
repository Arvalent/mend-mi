"""This is the Flask App."""
import os
import pymongo
from flask import Flask, jsonify, abort, request
from places_processing import extract_comments_serpapi_api

client = pymongo.MongoClient(
    os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/database")
)
db = client.get_database()

app = Flask(__name__)


def stringify_id(pymongo_dict):
	""" Converts the bson.objectid.ObjectId to a string,
		to allow for JSON serialization.
	"""
	return {key: str(pymongo_dict[key]) for key in pymongo_dict.keys()}


@app.errorhandler(404)
def resource_not_found(exception):
	"""Returns exceptions as part of a JSON."""
	return jsonify(error=str(exception)), 404


@app.route("/")
def main():
	"""Show the status of the app."""
	return "App is up!"


@app.route("/profile/<int:user_id>", methods=["GET"])
def get_profile(user_id):
	return {}


@app.route("/recommendations/<int:user_id>", methods=["GET"])
def create_recommendations(user_id):

	return {}


@app.route("/new_post/<int:user_id>", methods=["POST"])
def create_new_post(user_id):
	"""Takes a blog post via a POST request and inserts it into the database."""
	new_post = request.json
	new_post = new_post["User0"]
	if not new_post.get("registered_places", None) and not new_post.get("registered_images", None):
		return {"Error": "needs registered places and images to create demo user profile"}, 500

	# Add Recommendations based on registered Places and Tags
	places = new_post["registered_places"]
	for place in places.values():
		place_features = extract_comments_serpapi_api(place["search"], n_comments=20)
		place_features['google_id'] = place["search"]
		place_id = db.posts.insert_one(place_features).inserted_id
		place["id"] = place_id

		if place_features.get("similar_results", None):
			last_key = 0
			if new_post.get("recommendations", None):
				last_key = int(max(list(new_post["recommendations"].keys())))
			for i, [similar_id, similar_name] in enumerate(place_features["similar_results"].items()):
				new_post["recommendations"][str(i+last_key)] = {"id": similar_id, 'name': similar_name,
																'tags': place_features["type"],
																"original":{"google_id": place["search"],
																			"name": place_features['name']}}

	# one function: inputs urls images, output: embeddings: tensorflow pickle files

	# two functions: inputs tags, embeddings, location=str, outputs: {recommendation, tags}

	# Add Recommendations based on registered Images and Tags

	post_id = db.posts.insert_one(new_post).inserted_id
	return jsonify({"id": str(post_id)})


@app.route("/get_posts")
def get_posts():
	"""Gets all blog posts form the database."""
	posts_list = db.posts.find()
	try:
		if not posts_list:
			raise Exception("There are no posts in the database!")
		return jsonify([stringify_id(post) for post in posts_list])

	except Exception as exception:
		abort(404, exception)


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5001)

