#!/usr/bin/env python
# coding: utf-8
# Copyright 2013 Abram Hindle
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You can start this by executing it in python:
# python server.py
#
# remember to:
#     pip install flask


import flask
from flask import Flask, request
import json
app = Flask(__name__)
app.debug = True

# An example world
# {
#    'a':{'x':1, 'y':2},
#    'b':{'x':2, 'y':3}
# }

class World:
    def __init__(self):
        self.clear()
        
    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry

    def set(self, entity, data):
        self.space[entity] = data

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space

class Users:
    def __init__(self):
        self.users = {}
    
    def setWorld(self, id, world):
        self.users[id] = world

    def getWorld(self, id):
        return self.users[id]


# you can test your webservice from the commandline
# curl -v   -H "Content-Type: application/json" -X PUT http://127.0.0.1:5000/entity/X -d '{"x":1,"y":1}' 

myWorld = World()
listener = 1      
users = Users()

# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

# Home page. This is the usable draw board
@app.route("/")
def index():
    return flask.send_from_directory('static','index.html')

# Entity API (Post/Put only). This is the API which handles entity calls.
@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    try:
        # Post handler. Create a new entity
        if request.method == "POST":
            req_json = flask_post_json()
            # Check to see if the entity already exists. If it does exist, 
            # create a new entity with name X(length).
            if myWorld.get(entity) != {}:
                entity = "X" + str(len(myWorld.world()))
            myWorld.set(entity, req_json)
            # Return the entity using a direct call to the world to ensure that we are sending
            # the worlds data.
            return app.response_class(response=json.dumps(myWorld.get(entity)), mimetype='application/json')

        # Put handler. Update an existing entity
        elif request.method == "PUT":
            req_json = flask_post_json()
            # Update the entitys attributes given in the update request
            for key in req_json:
                myWorld.update(entity, key, req_json[key])
            # Return the entity using a direct call to the world to ensure that we are sending
            # the worlds data.
            return app.response_class(response=json.dumps(myWorld.get(entity)), mimetype='application/json')

    # Error handler
    except:
        return "Cannot update entity.", 400
    return None

# World API (Post/Get only). This API handles all calls to the world.
@app.route("/world", methods=['POST','GET'])    
def world():
    # Get handler. Returns the current world
    if request.method == 'GET':
        return app.response_class(response=json.dumps(myWorld.world()), mimetype='application/json')

    # Post handler. Sets the world to be the world given in the post body
    elif request.method == 'POST':
        try:
            req_json = flask_post_json()
            # Clear the world
            world.clear()
            # Set the world to be the world found in the post request
            for key in req_json:
                world.set(key, req_json[key])
            # Return the new world
            return app.response_class(response=json.dumps(myWorld.world()), mimetype='application/json')
        # Error handler
        except:
            return "Cannot update world.", 400
        
    else:
        return "Method not handled.", 500

# Entity Get handler. Gets a given entity's information
@app.route("/entity/<entity>")    
def get_entity(entity):
    if request.method == 'GET':
        return app.response_class(response=json.dumps(myWorld.get(entity)), mimetype='application/json')
    return "Method not handled.", 500

# Clear Post/Get API. Clears the world of all its contents.
@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    if request.method == 'GET' or request.method == 'POST':
        try:
            # Clear the world
            myWorld.clear()
            # Return the cleared world
            return app.response_class(response=json.dumps(myWorld.world()), mimetype='application/json')
        except:
            return "Cannot clear world.", 400
    return "Method not handled.", 500

# Listener GET API. Gets a new listener value which a client can use to
# get the worlds information based off of the last call it made to this listner.
@app.route("/listener", methods=["GET"])
def get_listener():
    # Global values which are being changed during this function call
    global listener
    global users
    if request.method == 'GET':
        # Setup the response
        response = {"listener": listener}
        # Create a new user at the current listener value with a blank world
        users.setWorld(str(listener), World())
        # Incriment listner value
        listener += 1
        # Return listner value which the user can call to get updates
        return app.response_class(response=json.dumps(response), mimetype='application/json') 
    else:
        return "Method not handled.", 500

# Listener/<listener> GET API. Gets the worlds values that may have changed since the
# last time this API was called.
@app.route("/listener/<listener>", methods=["GET"])
def get_diff(listener):
    # Global users is the only global value being changed
    global users
    if request.method == 'GET':
        try:
            # Setup the response, world and the users world
            response = {}
            world = myWorld.world()
            userWorld = users.getWorld(listener)
            userWorldValues = userWorld.world()


            # Check to see if there have been any changes to the world since the last time user world was called.
            # If there are changes, update the user world to be the same as the servers world.
            for key in world:
                if key not in userWorldValues or userWorldValues[key] != world[key]:
                    response[key] = world[key]
                    userWorld.set(key, world[key])
            # Check to see if the users world is somehow ahead of the servers world. If it is, send a refresh message.
            # This particular check works for when the world is cleared.
            for key in userWorldValues:
                if key not in world:
                    response["message"] = "refresh"
            return app.response_class(response=json.dumps(response), mimetype='application/json') 
        except:
            return "Invalid listener.", 400
    else:
        return "Method not handled.", 500


if __name__ == "__main__":
    app.run()
