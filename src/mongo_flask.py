"""This is the Flask App."""
import os
import pickle
from bson import ObjectId
import pymongo
from flask import Flask, jsonify, abort, request
from places_processing import extract_comments_serpapi_api
from produce_image_embeddings import *
from maps_research import get_location_local_results
from flask_cors import CORS


client = pymongo.MongoClient(
    os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/database")
)
db = client.get_database()
app = Flask(__name__)
CORS(app)


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


@app.route("/stored_places", methods=["GET"])
def return_places():
	places = {i: place for i, place in enumerate(db.places.find())}
	return places


@app.route("/profile/<string:user_id>", methods=["GET"])
def get_profile(user_id):
	""" Returns all tags linked to a user"""
	found_user = [user for user in db.users.find() if user["_id"] == ObjectId(f'{user_id}')]
	if found_user:
		user = found_user[0]
		return {user_id: user["profile"]}
	return {"Error": "User id not found in database"}


@app.route("/recommendations/<string:user_id>", methods=["GET"])
def get_recommendations(user_id):

	""" Returns all recommendations based on images provided by users and visited places"""
	found_user = [user for user in db.users.find() if user["_id"] == ObjectId(f'{user_id}')]
	if found_user:
		user = found_user[0]

		return {'place_recommendations': user["places_recommendations"],
				'images_recommendations': user["images_recommendations"]}
	return {"Error": "User id not found in database"}


@app.route("/new_post/<string:object_id>", methods=["POST"])
def create_new_post(object_id):
	"""Takes a blog post via a POST request and inserts it into the database."""

	new_post = request.json
	new_post["places_recommendations"] = {}
	new_post["images_recommendations"] = {}
	new_post["profile"] = []

	# if user do not exist
	found_user = [user for user in db.users.find() if user["_id"] == ObjectId(f'{object_id}')]
	if not found_user:
		if not new_post.get("registered_places", None) and not new_post.get("registered_images", None):
			return {"Error": "needs registered places and images to create demo user profile"}, 500

		# Add Recommendations based on registered Places and Tags
		places = new_post["registered_places"]
		for place in places.values():
			place_features = extract_comments_serpapi_api(place["search"], n_comments=20)
			place_features['google_id'] = place["search"]
			place_id = db.places.insert_one(place_features).inserted_id
			place["id"] = place_id

			if place_features.get("similar_results", None):
				last_key = 0
				if len(new_post.get("places_recommendations").keys()) > 0:
					last_key = int(max(list(new_post["places_recommendations"].keys())))
				for i, [similar_id, similar_name] in enumerate(place_features["similar_results"].items()):
					new_post["places_recommendations"][str(i+last_key)] = {"id": similar_id, 'name': similar_name,
																	'tags': place_features["type"][0],
																	"original":{"google_id": place["search"],
																				"name": place_features['name']}}
					new_post["profile"].extend([place_features["type"][0]])

		# inputs urls images, output: embeddings: tensorflow pickle file
		registered_images = [new_post['registered_images']]
		urls = [url['url'] for url in new_post['registered_images'].values()]
		tags_collection = [url['tags'] for url in new_post['registered_images'].values()]

		image_file_path = r"C:\Users\Lucas\Desktop\Lauzhack2022\mend-mi\data\images_test"
		files = [os.path.join(image_file_path, file) for file in os.listdir(image_file_path)
					if os.path.isfile(os.path.join(image_file_path, file))]

		embeddings = embeddings_from_images(files)
		with open(r"C:\Users\Lucas\Desktop\Lauzhack2022\mend-mi\data\embeddings.pickle", 'wb') as outfile:
			pickle.dump(embeddings, outfile)

		# two functions: inputs tags, embeddings, location=str, outputs: {recommendation, tags}
		coordinate_recommendation = []
		for i, tags in enumerate(tags_collection):
			for j, tag in enumerate(tags.split(",")):
				coordinate_recommendation = get_location_local_results(q=f"{tag} Lausanne")
				if not new_post.get("images_recommendations", None):
					new_post['images_recommendations'] = {}
				new_post['images_recommendations'].update({str(j+i*j): {"coordinates": coordinate_recommendation,
																		"tag": tag[0],
																		"original": urls[i]}})
				if j==0:
					new_post["profile"].extend([tag])

		recommendations = image_query(tags="", location="Lausanne", embeddings=embeddings)

		# Add Recommendations based on registered Images and Tags
		post_id = db.users.insert_one(new_post).inserted_id

		return jsonify({"id": str(post_id)})
	return {"Error": "User already exists"}


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
	db.create_collection("users")
	db.create_collection("places")

