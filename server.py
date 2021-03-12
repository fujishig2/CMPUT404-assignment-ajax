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

# you can test your webservice from the commandline
# curl -v   -H "Content-Type: application/json" -X PUT http://127.0.0.1:5000/entity/X -d '{"x":1,"y":1}' 

myWorld = World()          

# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

@app.route("/")
def index():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    return flask.send_from_directory('static','index.html')

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    try:
        if request.method == "POST":
            req_json = flask_post_json()
            if myWorld.get(entity) != {}:
                entity = "X" + str(len(myWorld.world()))
            myWorld.set(entity, req_json)
            return app.response_class(response=json.dumps(myWorld.get(entity)), mimetype='application/json')
        elif request.method == "PUT":
            req_json = flask_post_json()
            for key in req_json:
                myWorld.update(entity, key, req_json[key])
            return app.response_class(response=json.dumps(myWorld.get(entity)), mimetype='application/json')

    except:
        return "Cannot update entity.", 400
    return None

@app.route("/world", methods=['POST','GET'])    
def world():
    if request.method == 'GET':
        return app.response_class(response=json.dumps(myWorld.world()), mimetype='application/json')
    elif request.method == 'POST':
        try:
            req_json = flask_post_json()
            response = {}
            if req_json != myWorld.world():
                world = myWorld.world()
                for key in world:
                    if key not in req_json or req_json[key] != world[key]:
                        response[key] = world[key]
                for key in req_json:
                    if key not in world:
                        response[key] = ""
            return app.response_class(response=json.dumps(response), mimetype='application/json')
        except:
            return "Cannot update world.", 400
        
    else:
        return "Method not handled.", 500
        
    '''you should probably return the world here'''
    return None

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    if request.method == 'GET':
        return app.response_class(response=json.dumps(myWorld.get(entity)), mimetype='application/json')
    return "Method not handled.", 500

@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    if request.method == 'GET' or request.method == 'POST':
        try:
            myWorld.clear()
            return app.response_class(response=json.dumps(myWorld.world()), mimetype='application/json')
        except:
            return "Cannot clear world.", 400
    return "Method not handled.", 500


if __name__ == "__main__":
    app.run()
