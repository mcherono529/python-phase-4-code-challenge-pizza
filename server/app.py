#!/usr/bin/env python3
from flask import Flask, request, make_response, jsonify
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Restaurant, Pizza, RestaurantPizza
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)


@app.route("/")
def index():
    return "<h1>Code Challenge</h1>"


class RestaurantsResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return [restaurant.to_dict() for restaurant in restaurants], 200


class RestaurantByIdResource(Resource):
    def get(self, id):
        restaurant = db.session.get(Restaurant, id)
        if not restaurant:
            return {"error": "Restaurant not found"}, 404
        return restaurant.to_dict(rules=("-restaurant_pizzas.restaurant",)), 200

    def delete(self, id):
        restaurant = db.session.get(Restaurant, id) 
        if restaurant:
            for rp in restaurant.restaurant_pizzas:
                db.session.delete(rp)
            db.session.delete(restaurant)
            db.session.commit()
            return make_response("", 204)
        return make_response(jsonify({"error": "Restaurant not found"}), 404)


class PizzasResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [pizza.to_dict() for pizza in pizzas], 200


class RestaurantPizzasResource(Resource):
    def post(self):
        data = request.get_json()

        try:
            price = data.get("price")
            pizza_id = data.get("pizza_id")
            restaurant_id = data.get("restaurant_id")

            if price is None or pizza_id is None or restaurant_id is None:
                return {"errors": ["validation errors"]}, 400

            if not isinstance(price, (int, float)) or not (1 <= price <= 30):
                return {"errors": ["validation errors"]}, 400

            pizza = db.session.get(Pizza, pizza_id)
            restaurant = db.session.get(Restaurant, restaurant_id)
            if not pizza or not restaurant:
                return {"errors": ["validation errors"]}, 400

            new_restaurant_pizza = RestaurantPizza(
                price=price,
                restaurant_id=restaurant_id,
                pizza_id=pizza_id,
            )
            db.session.add(new_restaurant_pizza)
            db.session.commit()

            return new_restaurant_pizza.to_dict(rules=("-restaurant.restaurant_pizzas", "-pizza.restaurant_pizzas")), 201

        except Exception as e:
            return {"errors": ["An unexpected error occurred"]}, 500


api.add_resource(RestaurantsResource, "/restaurants")
api.add_resource(RestaurantByIdResource, "/restaurants/<int:id>")
api.add_resource(PizzasResource, "/pizzas")
api.add_resource(RestaurantPizzasResource, "/restaurant_pizzas")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
