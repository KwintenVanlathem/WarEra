from APIClient import APIClient
from Database import Database
import json
import schedule
import time
import urllib

def chunk_list(lst, size):
	for i in range(0, len(lst), size):
		yield lst[i:i + size]


def getUsersBatched(userIDs):
	result = []

	for part in chunk_list(userIDs, 100):
		procedures = ["user.getUserById"] * len(part)

		payload = {
			str(i): {
				"userId": str(userId)
			}
			for i, userId in enumerate(part)
		}

		encoded_input = urllib.parse.quote(json.dumps(payload))

		url = (
			"https://api2.warera.io/trpc/"
			+ ",".join(procedures)
			+ f"?batch=1&input={encoded_input}"
		)

		apiClient = APIClient()
		response = apiClient.get(url)

		for item in response:
			result.append(item)

	return result

def pullCitizens():
	apiClient = APIClient()
	procedure = "user.getUsersByCountry"
	payload = {
		"countryId": "6813b6d446e731854c7ac7a4", # Only Belgium for now
		"limit": 100,
	}
	users = apiClient.getByCursor(procedure, payload)

	userIDs = []
	for user in users:
		userIDs.append(user.get("_id"))

	users = getUsersBatched(userIDs)

	db = Database()
	db.updateUsers(users)
	db.addUsersRaw(users)

def updateCountries():
	apiClient = APIClient()
	procedure = "country.getAllCountries"
	payload = { }
	countries = apiClient.getSimple(procedure, payload)

	db = Database()
	db.updateCountries(countries)
	db.addCountriesRaw(countries)

def pullMoneyTransfers():
	apiClient = APIClient()
	procedure = "transaction.getPaginatedTransactions"
	payload = {
		"limit": 100,
		"transactionType": "countryMoneyTransfer"
	}
	moneyTransfers = apiClient.getByCursor(procedure, payload)

	db = Database()
	db.updateMoneyTransfers(moneyTransfers)

def getCountryBattlesBatched(countryIDs):
	db = Database()
	result = []

	for part in chunk_list(countryIDs, 10):
		procedures = ["battle.getBattles"] * len(part)

		payload = {
			str(i): {
				"isActive": True,
				"limit": 10,
				"filter": "all",
				"countryId": str(countryID)
			}
			for i, countryID in enumerate(part)
		}

		encoded_input = urllib.parse.quote(json.dumps(payload))

		url = (
			"https://api2.warera.io/trpc/"
			+ ",".join(procedures)
			+ f"?batch=1&input={encoded_input}"
		)

		apiClient = APIClient()
		response = apiClient.get(url)

		for item in response:
			for battle in item["result"]["data"]["items"]:
				result.append(battle)

	return(result)

def updateAlliedBattles():
	db = Database()
	countryIDs = db.getAlliedCountries()
	db.updateBattleHistory(getCountryBattlesBatched(countryIDs))

	recentBattles = db.getRecentBattles()

	procedures = ["battleRanking.getRanking"] * len(recentBattles)
	payload = {
		str(i): {
			"battleId": str(battleID),
			"dataType": "damage",
			"type": "country",
			"side": "attacker"
		}
		for i, battleID in enumerate(recentBattles)
	}

	apiClient = APIClient()
	result = apiClient.getBatched(procedures, payload)

	battleRanks = []
	for i in range(1, len(result)):
		battle = result[i]
		for rank in battle.get("rankings"):
			rank["battleID"] = recentBattles[i]
			rank["side"] = "attacker"
		battleRanks.extend(battle.get("rankings"))

	db.updateBattleDamageRankings(battleRanks)

	payload = {
		str(i): {
			"battleId": str(battleID),
			"dataType": "damage",
			"type": "country",
			"side": "defender"
		}
		for i, battleID in enumerate(recentBattles)
	}

	apiClient = APIClient()
	result = apiClient.getBatched(procedures, payload)

	battleRanks = []
	for i in range(1, len(result)):
		battle = result[i]
		for rank in battle.get("rankings"):
			rank["battleID"] = recentBattles[i]
			rank["side"] = "defender"
		battleRanks.extend(battle.get("rankings"))

	db.updateBattleDamageRankings(battleRanks)

	payload = {
		str(i): {
			"battleId": str(battleID),
			"dataType": "money",
			"type": "country",
			"side": "attacker"
		}
		for i, battleID in enumerate(recentBattles)
	}

	apiClient = APIClient()
	result = apiClient.getBatched(procedures, payload)

	battleRanks = []
	for i in range(1, len(result)):
		battle = result[i]
		for rank in battle.get("rankings"):
			rank["battleID"] = recentBattles[i]
			rank["side"] = "attacker"
		battleRanks.extend(battle.get("rankings"))

	db.updateBattleMoneyRankings(battleRanks)

	payload = {
		str(i): {
			"battleId": str(battleID),
			"dataType": "money",
			"type": "country",
			"side": "defender"
		}
		for i, battleID in enumerate(recentBattles)
	}

	apiClient = APIClient()
	result = apiClient.getBatched(procedures, payload)

	battleRanks = []
	for i in range(1, len(result)):
		battle = result[i]
		for rank in battle.get("rankings"):
			rank["battleID"] = recentBattles[i]
			rank["side"] = "defender"
		battleRanks.extend(battle.get("rankings"))

	db.updateBattleMoneyRankings(battleRanks)

def updateRegions():
	apiClient = APIClient()
	procedure = "region.getRegionsObject"
	payload = { }
	result = apiClient.getSimple(procedure, payload)

	regions = []
	for region in result:
		regions.append(result[region])

	db = Database()
	db.updateRegions(regions)


schedule.every().hour.at(":00").do(pullCitizens)
schedule.every().hour.at(":01").do(pullCitizens)
schedule.every().hour.at(":30").do(pullCitizens)
schedule.every().hour.at(":31").do(pullCitizens)

schedule.every(4).hours.at(":03").do(updateCountries)
schedule.every(4).hours.at(":05").do(pullMoneyTransfers)

schedule.every(2).hours.at(":07").do(updateAlliedBattles)

schedule.every().day.at("00:00").do(updateRegions)

while True:
	schedule.run_pending()
	time.sleep(1)
