import requests
import urllib
import json

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

	def getByCursor(this, procedure, payload):
		result = []
		
		cursor = None
		while True:
			if cursor:
				payload["cursor"] = cursor

			encoded_input = urllib.parse.quote(json.dumps(payload))
			
			url = (
				"https://api2.warera.io/trpc/"
				+ procedure
				+ f"?input={encoded_input}"
			)

			response = this.get(url)

			cursor = response["result"]["data"].get("nextCursor")
			result += response["result"]["data"]["items"]
			
			if not cursor:
				return result # dict of items

	def getSimple(this, procedure, payload):
		result = []

		encoded_input = urllib.parse.quote(json.dumps(payload))
		
		url = (
			"https://api2.warera.io/trpc/"
			+ procedure
			+ f"?input={encoded_input}"
		)

		response = this.get(url)

		return response["result"]["data"]

		
	def getBatched(this, procedures, payload):
		result = []

		encoded_input = urllib.parse.quote(json.dumps(payload))

		url = (
			"https://api2.warera.io/trpc/"
			+ ",".join(procedures)
			+ f"?batch=1&input={encoded_input}"
		)

		apiClient = APIClient()
		response = apiClient.get(url)
		
		for item in response:
			result.append(item["result"]["data"])
		
		return result