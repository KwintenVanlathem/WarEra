from APIClient import APIClient
from Database import Database
import json
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
			result.append(item["result"]["data"])

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
	db.addUsersRaw(users)

def pullMUs():
	apiClient = APIClient()
	procedure = "mu.getManyPaginated"
	payload = {
		"limit": 100,
	}
	mus = apiClient.getByCursor(procedure, payload)

	db = Database()
	db.updateMUs(mus)
	db.addMUsRaw(mus)

def pullPlayerHistory():
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

	usersRaw = getUsersBatched(userIDs)

	users = []
	for user in usersRaw:
		try:
			skillset = invested_points_by_category(user.get("skills"))

			info = {
				"id": user.get("_id"),
				"username": user.get("username"),
				"mu": user.get("mu"),
				"country": user.get("country"),
				"level": user.get("leveling", {}).get("level", 0),
				"isLeveling": user.get("leveling", {}).get("level", 0) < 20,
				"totalDamage": user.get("rankings", {}).get("userDamages", {}).get("value", 0),
				"moneyWealth": user.get("stats", {}).get("wealth", {}).get("money", 0),
				"itemWealth": user.get("stats", {}).get("wealth", {}).get("items", 0),
				"equipmentWealth": user.get("stats", {}).get("wealth", {}).get("equipments", 0),
				"weaponWealth": user.get("stats", {}).get("wealth", {}).get("weapons", 0),
				"companyWealth": user.get("stats", {}).get("wealth", {}).get("companies", 0),
				"totalWealth": user.get("stats", {}).get("wealth", {}).get("total", 0),
			}

			if user.get("buffs") == None:
				info["pillStatus"] = 'unpilled'
			elif user.get("buffs").get("buffCodes") != None:
				info["pillStatus"] = 'buff'
			elif user.get("buffs").get("debuffCodes") != None:
				info["pillStatus"] = 'debuff'

			if skillset.get("combat_pct") > 0.8:
				info["buildType"] = 'war'
			elif skillset.get("economic_pct") > 0.8:
				info["buildType"] = 'eco'
			else:
				info["buildType"] = 'hybrid'

			users.append(info)

		except:
			print(json.dumps(user, indent=2))
			raise

	db = Database()
	db.updateUsers(users)
	db.addUsersHistory(users)

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


def getBestRegions(itemCodes):
	regions = []

	procedures = ["company.getRecommendedRegionIdsByItemCode"] * len(itemCodes)

	payload = {
		str(i): {
			"itemCode": str(item),
			"includeDeposit": True
		}
		for i, item in enumerate(itemCodes)
	}

	apiClient = APIClient()
	result = apiClient.getBatched(procedures, payload)
	
	for i in range(1, len(result)):
		item = itemCodes[i]
		bonus = result[i][0]
		bonus["item"] = item
	
		regions.append(bonus)

	db = Database()
	db.updateBonus(regions)
	
def skill_points_from_level(level: int) -> int:
    """Returns the total skill points invested to reach a given level."""
    return level * (level + 1) // 2


def invested_points_per_skill(skills: dict) -> dict[str, int]:
    """
    Converts a skills JSON into invested skill points per skill.

    Args:
        skills: The skills JSON object.

    Returns:
        A dictionary mapping skill names to invested skill points.
    """
    return {
        skill_name: skill_points_from_level(skill_data.get("level", 0))
        for skill_name, skill_data in skills.items()
    }

ECONOMIC_SKILLS = {
    "energy",
    "companies",
    "entrepreneurship",
    "production",
    "management",
}

COMBAT_SKILLS = {
    "health",
    "hunger",
    "attack",
    "criticalChance",
    "criticalDamages",
    "armor",
    "precision",
    "dodge",
    "lootChance",
}


def invested_points_by_category(skills: dict) -> dict[str, int]:
    invested = invested_points_per_skill(skills)

    eco = sum(invested.get(skill, 0) for skill in ECONOMIC_SKILLS)
    combat = sum(invested.get(skill, 0) for skill in COMBAT_SKILLS)

    return {
        "economic": eco,
        "combat": combat,
        "total": eco + combat,
        "economic_pct": eco / (eco + combat) if eco + combat else 0,
        "combat_pct": combat / (eco + combat) if eco + combat else 0,
    }




