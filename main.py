from APIClient import APIClient
from Database import Database
import json
import schedule
import time
import urllib

def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def getByCursor(procedure, payload):
    apiClient = APIClient()
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

        response = apiClient.get(url)

        cursor = response["result"]["data"].get("nextCursor")
        result += response["result"]["data"]["items"]
        
        if not cursor:
            return result # dict of items

def getSimple(procedure, payload):
    apiClient = APIClient()
    result = []

    encoded_input = urllib.parse.quote(json.dumps(payload))
    
    url = (
        "https://api2.warera.io/trpc/"
        + procedure
        + f"?input={encoded_input}"
    )

    response = apiClient.get(url)

    return response["result"]["data"]

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
    procedure = "user.getUsersByCountry"
    payload = {
        "countryId": "6813b6d446e731854c7ac7a4", # Only Belgium for now
        "limit": 100,
    }
    users = getByCursor(procedure, payload)

    userIDs = []
    for user in users:
        userIDs.append(user.get("_id"))

    users = getUsersBatched(userIDs)

    db = Database()
    db.updateUsers(users)
    db.addUsersRaw(users)

def updateCountries():
    procedure = "country.getAllCountries"
    payload = { }
    countries = getSimple(procedure, payload)

    db = Database()
    db.updateCountries(countries)
    db.addCountriesRaw(countries)

def pullMoneyTransfers():
    procedure = "transaction.getPaginatedTransactions"
    payload = {
        "limit": 100,
        "transactionType": "countryMoneyTransfer"
    }
    moneyTransfers = getByCursor(procedure, payload)

    db = Database()
    db.updateMoneyTransfers(moneyTransfers)


schedule.every().hour.at(":00").do(pullCitizens)
schedule.every().hour.at(":01").do(pullCitizens)
schedule.every().hour.at(":30").do(pullCitizens)
schedule.every().hour.at(":31").do(pullCitizens)

schedule.every(4).hours.at(":03").do(updateCountries)
schedule.every(4).hours.at(":05").do(pullMoneyTransfers)

while True:
    schedule.run_pending()
    time.sleep(1)
