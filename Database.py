import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import pytz
import json
from config import config

class Database():
	instance = None

	dbConnection = psycopg2.connect(
		host = config["host"],
		dbname = config["dbname"],
		user = config["user"],
		password = config["password"],
	)

	def __new__(cls):
		if cls.instance is None:
			cls.instance = super().__new__(cls)
		return cls.instance

	def getAlliedCountries(this):
		countryIDs = []

		sql = """
			SELECT "countryID"
			FROM public.country
			WHERE "isAlly" = True;
		"""

		with this.dbConnection.cursor() as cur:
			cur.execute(sql)
			for country in cur.fetchall():
				countryIDs.append(country[0])

		return countryIDs


	def updateCountries(this, countries):
		rows = []
		for country in countries:
			rows.append((country.get("_id"), country.get("name"), False))

		sql = """
			INSERT INTO public.country ("countryID", name, "isAlly")
			VALUES %s
			ON CONFLICT ("countryID")
			DO UPDATE SET
				name = EXCLUDED.name;
		"""

		with this.dbConnection.cursor() as cur:
			execute_values(cur, sql, rows)
			this.dbConnection.commit()

	def addCountriesRaw(this, countries):
		rows = []
		for country in countries:
			rows.append((datetime.now(pytz.utc), country.get("_id"), country.get("name"), json.dumps(country)))

		sql = """
			INSERT INTO public."countryRaw" ("timestamp", "countryID", "name", "value")
			VALUES %s;
		"""

		with this.dbConnection.cursor() as cur:
			execute_values(cur, sql, rows)
			this.dbConnection.commit()


	def updateUsers(this, users):
		rows = []
		for user in users:
			rows.append((user["result"]["data"].get("_id"), user["result"]["data"].get("username")))

		sql = """
			INSERT INTO public.user ("userID", name)
			VALUES %s
			ON CONFLICT ("userID")
			DO UPDATE SET
				name = EXCLUDED.name;
		"""

		with this.dbConnection.cursor() as cur:
			execute_values(cur, sql, rows)
			this.dbConnection.commit()

	def addUsersRaw(this, users):
		rows = []
		for user in users:
			rows.append((datetime.now(pytz.utc), user["result"]["data"].get("_id"), json.dumps(user)))

		sql = """
			INSERT INTO public."userRaw" ("eventTime", "userID", "value")
			VALUES %s;
		"""

		with this.dbConnection.cursor() as cur:
			execute_values(cur, sql, rows)
			this.dbConnection.commit()


	def updateMoneyTransfers(this, moneyTransfers):
		rows = []
		for transfer in moneyTransfers:
			rows.append((transfer.get("_id"), transfer.get("sellerCountryId"), transfer.get("buyerCountryId"), transfer.get("money"), transfer.get("createdAt")))

		sql = """
			INSERT INTO public."countryMoneyTransfer" ("id", "from", "to", "money", "timestamp")
			VALUES %s
			ON CONFLICT ("id")
			DO UPDATE SET
				"from" = EXCLUDED.from,
				"to" = EXCLUDED.to,
				"money" = EXCLUDED.money,
				"timestamp" = EXCLUDED.timestamp;
		"""

		with this.dbConnection.cursor() as cur:
			execute_values(cur, sql, rows)
			this.dbConnection.commit()

			
	def getRecentBattles(this):
		battleIDs = []

		sql = """
			SELECT "battleID"
			FROM public."battleHistory"
			WHERE "createdAt" > now() - interval '40 hours';
		"""

		with this.dbConnection.cursor() as cur:
			cur.execute(sql)
			for battle in cur.fetchall():
				battleIDs.append(battle[0])

		return battleIDs

	def updateBattleHistory(this, battles):
		rows = []
		knownBattles = []
		for battle in battles:
			if battle.get("_id") not in knownBattles:
				rows.append((battle.get("_id"), battle.get("createdAt"), battle.get("attacker").get("country"), battle.get("defender").get("country"), json.dumps(battle), battle.get("defender").get("region")))
				knownBattles.append(battle.get("_id"))

		sql = """
			INSERT INTO public."battleHistory" ("battleID", "createdAt", "attackerID", "defenderID", "value", "regionID")
			VALUES %s
			ON CONFLICT ("battleID")
			DO UPDATE SET
				value = EXCLUDED.value,
				"regionID" = EXCLUDED."regionID";
		"""

		with this.dbConnection.cursor() as cur:
			execute_values(cur, sql, rows)
			this.dbConnection.commit()

	def updateBattleDamageRankings(this, battleRanks):
		rows = []
		for battleRank in battleRanks:
			rows.append((battleRank.get("battleID"), battleRank.get("country"), battleRank.get("side"), battleRank.get("value"), battleRank.get("rank")))

		sql = """
			INSERT INTO public."battleCountryDamage" ("battleID", "countryID", "side", "damage", "rank")
			VALUES %s
			ON CONFLICT ("battleID", "countryID", "side")
			DO UPDATE SET
				damage = EXCLUDED.damage,
				rank = EXCLUDED.rank;
		"""

		with this.dbConnection.cursor() as cur:
			execute_values(cur, sql, rows)
			this.dbConnection.commit()

	def updateBattleMoneyRankings(this, battleRanks):
		rows = []
		for battleRank in battleRanks:
			rows.append((battleRank.get("battleID"), battleRank.get("country"), battleRank.get("side"), battleRank.get("value"), battleRank.get("rank")))

		sql = """
			INSERT INTO public."battleCountryMoney" ("battleID", "countryID", "side", "money", "rank")
			VALUES %s
			ON CONFLICT ("battleID", "countryID", "side")
			DO UPDATE SET
				money = EXCLUDED.money,
				rank = EXCLUDED.rank;
		"""

		with this.dbConnection.cursor() as cur:
			execute_values(cur, sql, rows)
			this.dbConnection.commit()

	def updateRegions(this, regions):
		rows = []
		for region in regions:
			rows.append((region.get("_id"), region.get("country"), region.get("name")))

		sql = """
			INSERT INTO public.region ("regionID", "countryID", name)
			VALUES %s
			ON CONFLICT ("regionID")
			DO UPDATE SET
				"countryID" = EXCLUDED."countryID",
				name = EXCLUDED.name;
		"""

		with this.dbConnection.cursor() as cur:
			execute_values(cur, sql, rows)
			this.dbConnection.commit()
