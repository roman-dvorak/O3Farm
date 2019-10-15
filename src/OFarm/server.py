
from flask import Flask
from flask import request
from flask import render_template
from flask import redirect
from flask import url_for
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from flask import json
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler
import requests

import pymongo
import json
import bson
import bson.json_util

import time
import datetime
import os 
import sys

import requests
from .api import Api

from OFarm.printer import *


class printer():
    def __init__(self, name, url, api_key):
        self.name = name
        self.url = url
        self.api_key = api_key

    def get_version(self):
        headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': self.api_key
            }
        print("ZJISTI STAV!", self.url+"/api/version")
        response = requests.get(self.url+"/api/version", headers=headers)
        return(str(response.content))




class server():
    def __init__(self):
        print("Start server")

        self.printers = []
        self.printer_class = {}

        self.db = pymongo.MongoClient('localhost', 27017)['OFarm']

        self.pf = PrinterFarm(self.db)
        #self.pf.start()
        self.api = Api(self.db)
        self.app = Flask('OFarm')
        self.start()

        self.app.config['TEMPLATES_AUTO_RELOAD'] = True
        self.app.config['TESTING'] = True
        self.app.config['DEBUG'] = True
        self.app.config['ENV'] = "development"
        self.app.run(host="0.0.0.0", port=9006)



    def start(self):

        self.pf.load_printers()
        #self.load_printers()
        
        self.queue = Queue(connection=Redis())
        self.scheduler = Scheduler(connection=Redis())

        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/printers', 'printers', self.get_printers)
        self.app.add_url_rule('/printer/<id>/', 'printer', self.printer)

        self.api.add_rules(self.app)
        self.pf.add_rules(self.app)


    def index(self):
        print(request)
        print(request.json)
        print(request.data)
        #result = self.queue.enqueue(long)
        return render_template('index.html', title='Home')


    def get_printers(self, status = True):
        response = self.app.response_class(
            response=bson.json_util.dumps(self.pf.get_printers(update = True)),
            status=200,
            mimetype='application/json'
        )
        return response

    def printer(self, id):
        id = bson.ObjectId(id)
        p = self.pf.get_printer(id, update = True)
        print(p['name'])
        return(bson.json_util.dumps(p))
