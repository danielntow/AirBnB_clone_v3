#!/usr/bin/python3
"""
Places view
"""

from flask import Flask, jsonify, request, abort
from api.v1.views import app_views
from models import storage
from models.place import Place
from models.city import City
from models.user import User
from models.state import State
from models.amenity import Amenity

app = Flask(__name__)


@app_views.route('/cities/<city_id>/places', methods=['GET'], strict_slashes=False)
def get_places(city_id):
    """Retrieves the list of all Place objects of a City"""
    city = storage.get(City, city_id)
    if city is None:
        abort(404)
    places = [place.to_dict() for place in city.places]
    return jsonify(places)


@app_views.route('/places/<place_id>', methods=['GET'], strict_slashes=False)
def get_place(place_id):
    """Retrieves a Place object"""
    place = storage.get(Place, place_id)
    if place is None:
        abort(404)
    return jsonify(place.to_dict())


@app_views.route('/places/<place_id>', methods=['DELETE'], strict_slashes=False)
def delete_place(place_id):
    """Deletes a Place object"""
    place = storage.get(Place, place_id)
    if place is None:
        abort(404)
    storage.delete(place)
    storage.save()
    return jsonify({})


@app_views.route('/cities/<city_id>/places', methods=['POST'], strict_slashes=False)
def create_place(city_id):
    """Creates a Place"""
    city = storage.get(City, city_id)
    if city is None:
        abort(404)
    content = request.get_json()
    if content is None:
        abort(400, "Not a JSON")
    if 'user_id' not in content:
        abort(400, "Missing user_id")
    if 'name' not in content:
        abort(400, "Missing name")
    user = storage.get(User, content['user_id'])
    if user is None:
        abort(404)
    new_place = Place(city_id=city_id, **content)
    new_place.save()
    return jsonify(new_place.to_dict()), 201


@app_views.route('/places/<place_id>', methods=['PUT'], strict_slashes=False)
def update_place(place_id):
    """Updates a Place object"""
    place = storage.get(Place, place_id)
    if place is None:
        abort(404)
    content = request.get_json()
    if content is None:
        abort(400, "Not a JSON")
    for key, value in content.items():
        if key not in ['id', 'user_id', 'city_id', 'created_at', 'updated_at']:
            setattr(place, key, value)
    place.save()
    return jsonify(place.to_dict())


def filter_places_by_states_cities(states, cities):
    """Filter places based on states and cities."""
    places = set()
    for state_id in states:
        state = storage.get(State, state_id)
        if state:
            places.update(state.places)
    for city_id in cities:
        city = storage.get(City, city_id)
        if city:
            places.update(city.places)
    return places


def filter_places_by_amenities(places, amenities):
    """Filter places based on amenities."""
    if amenities:
        amenities_set = set(amenities)
        places = [place for place in places if all(
            amenity.id in amenities_set for amenity in place.amenities)]
    return places


@app_views.route('/places_search', methods=['POST'], strict_slashes=False)
def places_search():
    """Search for places based on JSON content."""
    request_json = request.get_json()
    if not request_json:
        return jsonify({"error": "Not a JSON"}), 400

    states = request_json.get('states', [])
    cities = request_json.get('cities', [])
    amenities = request_json.get('amenities', [])

    if not states and not cities:
        places = storage.all(Place).values()
    else:
        places = filter_places_by_states_cities(states, cities)

    places = filter_places_by_amenities(places, amenities)

    places_list = [place.to_dict() for place in places]
    return jsonify(places_list)


@app_views.route('/places_searched', methods=['POST'], strict_slashes=False)
def places_searched():
    """Search for places based on JSON content."""
    request_json = request.get_json()
    if not request_json:
        return jsonify({"error": "Not a JSON"}), 400

    states = request_json.get('states', [])
    cities = request_json.get('cities', [])
    amenities = request_json.get('amenities', [])

    if not states and not cities:
        places = storage.all(Place).values()
    else:
        places = set()
        for state_id in states:
            state = storage.get(State, state_id)
            if state:
                places.update(state.places)
        for city_id in cities:
            city = storage.get(City, city_id)
            if city:
                places.update(city.places)

    if amenities:
        amenities_set = set(amenities)
        places = [place for place in places if all(
            amenity.id in amenities_set for amenity in place.amenities)]

    places_list = [place.to_dict() for place in places]
    return jsonify(places_list)


@app_views.route('/places_searches', methods=['POST'], strict_slashes=False)
def places_searches():
    """Searches for places based on JSON in the request body"""

    try:
        search_params = request.get_json()
    except Exception:
        abort(400, "Not a JSON")

    if not search_params or not any(search_params.values()):
        places = storage.all(Place).values()
        return jsonify([place.to_dict() for place in places])

    states = search_params.get('states', [])
    cities = search_params.get('cities', [])
    amenities = search_params.get('amenities', [])

    if not isinstance(states, list) or not isinstance(cities, list) or not isinstance(amenities, list):
        abort(400, "Invalid JSON")

    places_result = set()

    # Filter places by states
    for state_id in states:
        state = storage.get(State, state_id)
        if state:
            places_result.update(state.places)

    # Filter places by cities
    for city_id in cities:
        city = storage.get(City, city_id)
        if city:
            places_result.update(city.places)

    # Filter places by amenities
    if amenities:
        amenities_set = set(amenities)
        places_result = [
            place for place in places_result if amenities_set.issubset(place.amenities)]

    return jsonify([place.to_dict() for place in places_result])
