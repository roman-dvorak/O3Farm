import bson
import datetime
from flask import request
from flask import redirect
from flask import url_for
import os
import json
import time

class Api():
    def __init__(self, db):
        self.db = db

    def add_rules(self, app):
        app.add_url_rule('/api/version', 'api_version', self.version)
        app.add_url_rule('/api/files/<location>', 'files_upload_location', self.files_upload, methods=["POST"])
        app.add_url_rule('/api/files', 'files_upload', self.files_upload, methods=["POST"])
        app.add_url_rule('/api/files', 'files', self.files, methods=["GET"])
        app.add_url_rule('/api/query', 'query', self.query, methods=["GET"])
        app.add_url_rule('/api/query', 'query_set', self.query_set, methods=["POST"])

    def version(self):
        return {
            "api": "0.1",
            "server": "1.3.11",
            #"text": "OFarm - Octoprint connector"
            "text": "OctoPrint 1.3.11"
        }


    def files_upload(self, location = None):
        file = request.files['file']
        file.save(os.path.join("/home/roman/upload/", file.filename))
        print("UKLADAM SOUBOR")
        data = {
            'name': file.filename,
            'file': file.filename,
            'type': '',
            'size': 0,
            'date': time.time(),
            'typePath': '',
            'hash': '',
            'origin': 'local',
            'refs': {}
        }
        self.db.files.update_one({"_id": file.filename},{"$set":data}, upsert = True)

        return redirect(url_for('index'))


    def files(self):
        files = json.loads(bson.json_util.dumps(self.db.files.find()))
        data = {
            'files': files,
            'free': "999.99GB"
        }
        return data

    def query(self):
        pass

    def query_set(self):
        data = json.loads(request.data)

        row = {
            'file_id': data['id'],
            'created': time.time(),
            'state': 'created',
            'print_info': {}
        }
        self.db.print_query.insert_one(row)
        print(data)
        return {"state": "ok"}
        

