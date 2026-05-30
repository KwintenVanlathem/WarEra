import requests
from config import config

class APIClient():
	instance = None
	apiKey = config["apiKey"]

	def __new__(cls):
		if cls.instance is None:
			cls.instance = super().__new__(cls)
		return cls.instance

	def get(this, url):
		headers = {
			"X-API-Key": this.apiKey,
			"Content-Type": "application/json"
		}
		response = requests.get(url, headers=headers)
		response.raise_for_status()
		return response.json()