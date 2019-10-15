
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

        self.pf = PrinterFarm()
        self.api = Api()
        self.app = Flask('OFarm')
        self.start()

        self.app.run(host="0.0.0.0", port=9006)



    def start(self):
        self.db = pymongo.MongoClient('localhost', 27017)['OFarm']

        self.load_printers()
        
        self.queue = Queue(connection=Redis())
        self.scheduler = Scheduler(connection=Redis())
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/upload', 'upload', self.upload_file, methods=["GET", "POST"])
        self.app.add_url_rule('/get_files', 'get_files', self.get_files)
        self.app.add_url_rule('/printers', 'printers', self.get_printers)
        self.app.add_url_rule('/printer/<id>/', 'printer', self.printer)

        self.api.add_rules(self.app)

    def load_printers(self):
        print("Load printers")
        printers = list(self.db.printers.find())
        self.printers = printers

        for printer in self.printers:
            if printer['_id'] not in self.printer_class:
                #TODO: handle different API types for other printers
                print("loading printer", printer['name'])
                self.printer_class[printer['_id']] = {}
                self.printer_class[printer['_id']]['class'] = OctoprintPrinter()
                self.printer_class[printer['_id']]['class'].load_from_db(printer)
                #self.printer_class[printer['_id']]['printer'] = self.printer_class[printer['_id']]['class'].get_info()
                #self.printer_class[printer['_id']]['status'] = self.printer_class[printer['_id']]['class'].get_status()

    def update_printers(self):
        for p in self.printer_class:
            self.printer_class[p]['class'].update()


    def index(self):
        print(request)
        print(request.json)
        print(request.data)
        #result = self.queue.enqueue(long)
        return render_template('index.html', title='Home')


    def get_printers(self, status = True):
        self.update_printers()
        out = []

        for p in self.printers:
            ps = {}
            ps['info'] = self.printer_class[p['_id']]['class'].get_info()
            ps['status'] = self.printer_class[p['_id']]['class'].get_status()
            out.append(ps)

        response = self.app.response_class(
            response=bson.json_util.dumps(out),
            status=200,
            mimetype='application/json'
        )
        return response

    def printer(self, id):
        id = bson.ObjectId(id)
        p = self.printer_class[id]['class']
        print(p.name)
        return(p.get_status(update = True))


    def upload_file(self):
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            print(file)
            print(file.filename)
            
            file.save(os.path.join("/home/roman/upload/", file.filename))
            return redirect(url_for('index'))
        #return 'ok'

    def get_files(self):
        lsdir = os.listdir('/home/roman/upload')
        dirs = {}
        for f in lsdir:
            dirs[f] = {}

        return dirs