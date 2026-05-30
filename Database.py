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