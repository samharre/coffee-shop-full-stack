import os
import json
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

# ROUTES
@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        drinks = Drink.query.order_by(Drink.title).all()


        return jsonify({
            'success': True,
            'drinks': [drink.short() for drink in drinks]
        })
    except:
        abort(500)


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt_payload):
    try:
        drinks = Drink.query.order_by(Drink.title).all()

        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in drinks]
        })
    except:
        abort(500)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt_payload):
    body = request.get_json()

    if not ('title' in body and 'recipe' in body):
        abort(422)

    title = body.get('title')
    recipe = body.get('recipe')

    try:
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except:
        abort(500)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt_payload, drink_id):
    body = request.get_json()
    if not ('title' in body or 'recipe' in body):
        abort(422)

    drink = Drink.query.get(drink_id)
    if not drink:
        abort(404)

    try:
        title = body.get('title')
        recipe = body.get('recipe')

        if title:
            drink.title = title

        if recipe:
            drink.recipe = json.dumps(recipe)

        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except:
        abort(500)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt_payload, drink_id):
    drink = Drink.query.get(drink_id)
    if not drink:
        abort(404)

    try:
        drink.delete()

        return jsonify({
            'success': True,
            'delete': drink_id
        })
    except:
        abort(500)


# Error Handling
def format_error(status_code, message):
    return jsonify({
        'success': False,
        'error': status_code,
        'message': message
    }), status_code


@app.errorhandler(400)
def bad_request(error):
    return format_error(400, "Bad request")


@app.errorhandler(404)
def not_found(error):
    return format_error(404, "Resource not found")


@app.errorhandler(405)
def method_not_allowed(error):
    return format_error(405, "Method not allowed")


@app.errorhandler(422)
def unprocessable(error):
    return format_error(422, "Unprocessable")


@app.errorhandler(500)
def server_error(error):
    return format_error(500, 'Internal server error')


@app.errorhandler(AuthError)
def handle_auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        'message': error.error['description']
    }), error.status_code
