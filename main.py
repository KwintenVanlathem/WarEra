from ETL import *
import schedule
import time

schedule.every().hour.at(":00").do(getWars)
schedule.every().hour.at(":00").do(pullCitizens)
schedule.every().hour.at(":01").do(pullCitizens)
schedule.every().hour.at(":30").do(pullCitizens)
schedule.every().hour.at(":31").do(pullCitizens)

schedule.every().hour.at(":15").do(pullPlayerHistory)
schedule.every().hour.at(":45").do(pullPlayerHistory)

schedule.every(4).hours.at(":03").do(updateCountries)
schedule.every(4).hours.at(":05").do(pullMoneyTransfers)

schedule.every().day.at("00:00").do(updateRegions)
schedule.every().day.at("00:00").do(pullMUs)

while True:
	schedule.run_pending()
	time.sleep(1)
