import json
import requests
import datetime


class GenericPrinter(object):
	def __init__(self):
		self.platform = 'generic'
		self.name = 'Generic printer'
		self.last_update = None
		self.url = ''
		self.status = {
		    "text": "OF disconnected",
		    "flags": {
				'online': False,
				'printing': False,
				"operational": False,
				"paused": False,
				"printing": False,
				"cancelling": False,
				"pausing": False,
				"sdReady": False,
				"error": False,
				"ready": False,
				"closedOrError": False
			}
		}

	def load_from_db(self, db):
		self.id = db['_id']
		self.name = db['name']
		self.platform = db['platform']
		self.api_key = db['api_key']
		self.url = db['url']

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
		headers = {
			'Content-Type': 'application/json',
			'X-Api-Key': self.api_key
		}
		return requests.get(self.url+url, headers=headers).json()


	def get_version(self):
		response = self.make_request('/api/version')
		return(str(response))


	def get_status(self, update = False):
		if update:
			printer = self.make_request('/api/printer')
			job = self.make_request('/api/job')
			self.status = {**printer, **job}
			self.last_update = datetime.datetime.now()

		return self.status
		