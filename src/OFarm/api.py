
from flask import request
import os

class Api():
    def __init__(self):
        pass

    def add_rules(self, app):
        app.add_url_rule('/api/version', 'api_version', self.version)
        app.add_url_rule('/api/files/<location>', 'files', self.files, methods=["GET", "POST"])

    def version(self):
        return {
                    "api": "0.1",
                    "server": "1.3.11",
                    #"text": "OFarm - Octoprint connector"
                    "text": "OctoPrint 1.3.11"
                }

    def files(self, location = 'local'):
        #print(request.headers)
        file = request.files['file']
        file.save(os.path.join("/home/roman/upload/", file.filename))

        return {'done': True}