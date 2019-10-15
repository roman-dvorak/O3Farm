import json
import requests
import datetime
import threading
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler
import datetime
from flask import request
from flask import jsonify
import os
import bson

class PrinterFarm(object):

    states = ['Disabled', 'Offline', 'Ready', 'Printing', 'Done', 'Error']

    def __init__(self, db):
        self.printers = {}
        self.objects = {}
        self.db = db


    def add_printer(self, printer):
        pass

    def add_rules(self, app):
        app.add_url_rule('/api/of/eneable', 'set_eneable', self.set_eneable, methods=["POST"])

    def load_printers(self, id = None):
        if id is None:
            printers = list(self.db.printers.find())
            self.printers = printers
            for p in printers:
                if p['_id'] not in self.objects:
                    self.objects[p['_id']] = OctoprintPrinter()
                    self.objects[p['_id']].load_from_db(p)
                    self.objects[p['_id']].init()
            return True

    def set_eneable(self):
        args =  json.loads(request.data)
        id = bson.ObjectId(args['id'])
        self.objects[id].disabled = not args['eneable']
        self.db.printers.update(
            {"_id": id},
            {'$set': {'disabled': not args['eneable']}}
        )
        return {"status": "ok"}



    def get_printer(self, id, update = False):
        if update:
            self.update_printers(id)
        printers = dict(self.db.printers.find_one({"_id": id}))
        print(printers)
        return printers

    def get_printers(self, update = True):
        if update:
            self.update_printers()
        out = list(self.db.printers.find())
        for p in out:
            p['local_state_text'] = self.states[p['local_state']]
        return out


    #TODO: Allow to update only one printer
    def update_printers(self, id = None):
        for p in self.objects:
            out = self.objects[p].update()
            print(out)

            self.db.printers.update({"_id": p},
                {
                    '$set':{
                        #'info': info,
                        'status': self.objects[p].get_status(),
                        'last_update': self.objects[p].last_update,
                        'local_state': self.objects[p].local_state,
                        'disabled': self.objects[p].disabled,
                        'online': self.objects[p].online
                    }
                })


'''
    local_status:
        0- Disabled - light-gray
        1 - Offline - gray
        2 - Ready - green
        3 - Printing - blue
        4 - Post printing - orange
        5 - Error - red


'''

class GenericPrinter(object):
    def __init__(self):
        self.platform = 'generic'
        self.name = 'Generic printer'
        self.last_update = None
        self.url = ''
        self.api_key = ''
        self.id = ''
        self.local_state = 0;
        self.disabled = True
        self.online = False
        self.connected = False
        self.status = {}


    def init(self):
        self.get_version()

    def load_from_db(self, db):
        self.id = db['_id']
        self.name = db['name']
        self.platform = db['platform']
        self.api_key = db['api_key']
        self.url = db['url']
        self.disabled= db.get('disabled', True)
        self.last_update = datetime.datetime(year = 1997, month = 1, day = 1)

    def get_version(self):
        pass

    def get_name(self):
        return self.name

    def get_platform(self):
        return self.platform

    def get_url(self):
        return self.url

    def get_status(self, update = False):
        if update:
            #TODO: Update values
            pass
        return self.status

    def get_info(self):
        return {
            'name': self.name,
            'url': self.url,
            'platform': self.platform,
            'last_update': self.last_update,
            'id': str(self.id)
        }
        # tady budou informace o tom, co je to za tiskarnu atd..

    def set_logger(self, callback, id):
        pass

    def update(self):
        self.get_status(update = True);
        return True


class OctoprintPrinter(GenericPrinter):
    
    def __init__(self):
        super(OctoprintPrinter, self).__init__()

    def make_request(self, url):
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Api-Key': self.api_key
            }
            data = requests.get(self.url+url, headers=headers).json()
            self.last_update = datetime.datetime.now()
            self.online = True

        except (requests.exceptions.ConnectionError) as e:
            print(e)
            print("Connection is not possible, switching to 'OFFLINE")
            self.online = False
            data = False

        return data


    def get_version(self):
        response = self.make_request('/api/version')
        return(str(response))


    def get_status(self, update = False):
        if update:
            printer = self.make_request('/api/printer')
            job = self.make_request('/api/job')
            if printer and job:
                self.status = {**printer, **job}
                self.status['local_state'] = self.local_state
                #self.last_update = datetime.datetime.now()

        return self.status
        