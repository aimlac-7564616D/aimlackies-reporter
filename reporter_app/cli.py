from flask_security import hash_password
from sqlalchemy.sql import func
from reporter_app import db
from reporter_app.models import ElecUse, Co2, ElecGen, RealPowerReadings, RealSiteReadings, Trading,PredictedPrice, ClearoutPrice
from reporter_app.electricity_use.utils import call_leccyfunc
from reporter_app.electricity_gen.utils import get_energy_gen
from reporter_app.rse_api.utils import get_device_power, get_site_info, get_bids,get_clearout , post_bids
from reporter_app.trading.utils import get_predicted_price

from datetime import datetime, timedelta, date, time
import json
import requests


def register(app, user_datastore):
	@app.cli.command("seed")
	def seed():
		"""
		Seed database with all roles and an admin user
		"""
		roleAdmin = user_datastore.create_role(
			name='admin',
			description='Manage other users on the system')
		roleStandard = user_datastore.create_role(
			name='standard',
			description='Manage the system')
		roleVerified = user_datastore.create_role(
			name='verified',
			description='User has been verified and can use the system')
		userAdmin = user_datastore.create_user(
			username='admin',
			first_name='admin',
			surname='admin',
			email='admin@aimlackies.com',
			password=hash_password('password'),
			confirmed_at=func.now()
		)
		userAdmin.roles.append(roleAdmin)
		userAdmin.roles.append(roleVerified)
		db.session.commit()

		print("Created seed user data")

	@app.cli.command("generate_elec_use_data")
	def generate_elec_use_data():
		"""
		Grab electricity usage data and add it to electricity use DB table
		"""

		# grab elctricity usage data
		e_use_df = call_leccyfunc()

		# write elctricity usage data to database
		for idx, row in e_use_df.iterrows():
			newElecUse = ElecUse(
				date_time=row['Time'],
				electricity_use=row['Electricity Usage (kW)']
			)
			if ElecGen.query.get(newElecUse.date_time) is None:
				db.session.add(newElecUse)
		db.session.commit()

	@app.cli.command("elec_gen")
	def elecGen():

		# grab elctricity elec gen data
		e_gen_df = get_energy_gen()

		latest_elec_use_entery = ElecGen.query.order_by(ElecGen.date_time.desc()).first()

		# write elctricity gen data to database
		numOfTurbunes = 6  #2 Originals plus 2 extra Ed mentioned...?
		panel_area = 877 # Not sure where Lukas gets this from
		for idx, row in e_gen_df.iterrows():
			# add entery to database if no prediction already made for timestamp
			if (latest_elec_use_entery is None) or (datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S') > latest_elec_use_entery.date_time):
				newElecGen = ElecGen(
					date_time=row['time'],
					wind_gen=row['windenergy'] * numOfTurbunes,
					solar_gen=row['totalSolarEnergy'] * panel_area
				)
				if ElecGen.query.get(newElecGen.date_time) is None:
					db.session.add(newElecGen)
		db.session.commit()


	@app.cli.command("co2_for_time")
	def co2ForTime():
		'''
		Looks up CO2 intensity from api.carbonintensity.org and writes to the database
		'''
		#rounds the current time down to nearest 30 minutes (to allow for database relationship with electricity usage
		now = datetime.now()
		start = now - (now - datetime.min) % timedelta(minutes=30)

		print("start:", start)

		#Get date and format it for url
		end = start + timedelta(minutes=30) #api requires an end time as well, so add 30 minutes to the start time
		url=("https://api.carbonintensity.org.uk/regional/intensity/" + str(start.strftime("%Y-%m-%dT%H:%MZ")) + "/" + str(end.strftime("%Y-%m-%dT%H:%MZ")) + "/regionid/7")
		#print(url)

		#Fetch data from from API
		response = requests.get(url)

		#select co2 forecast from within json data
		data = response.json()
		co2Forecast = data["data"]["data"][0]["intensity"]["forecast"]

		newCo2Value = Co2(
			date_time=start,
			co2=co2Forecast
		)

		if Co2.query.get(newCo2Value.date_time) is None:
			db.session.add(newCo2Value)
		db.session.commit()

		print ("For the 30-min time period starting:", start, "the grid CO2 intensity (gCO2/kWh) was:", co2Forecast)

	@app.cli.command("get_real_power")
	def getRealPower():

		# [device name, true if generates power; false if consumes it]
		devices = [
			["Llanwrtyd Wells - Computing Centre", False],
			["Llanwrtyd Wells - Solar Generator", True],
			["Llanwrtyd Wells - Wind Generator 1", True],
			["Llanwrtyd Wells - Wind Generator 2", True],
			["Llanwrtyd Wells - Wind Generator 3", True],
			["Llanwrtyd Wells - Wind Generator 4", True],
			["Llanwrtyd Wells - Wind Generator A", True],
			["Llanwrtyd Wells - Wind Generator B", True],
		]

		for device in devices:
			stats = get_device_power(device[0])
			newPowerReading = RealPowerReadings(
				date_time=stats['datetime'],
				power=stats['power'],
				device_name=device[0],
				power_generator=device[1]
			)
			if RealPowerReadings.query.get((
				newPowerReading.date_time,
				newPowerReading.device_name
			)) is None:
				db.session.add(newPowerReading)
		db.session.commit()

	@app.cli.command("get_real_site_info")
	def getRealSiteInfo():

		stats = get_site_info()
		newSiteInfo = RealSiteReadings(
			date_time=stats['datetime'],
			power=stats['power'],
			temperature=stats['temperature']
		)
		if RealSiteReadings.query.get(newSiteInfo.date_time) is None:
			db.session.add(newSiteInfo)
		db.session.commit()

	@app.cli.command("predict_price")
	def predictPrice():
		'''
		Looks up predicted load and predicts price
		'''
		reported_date=datetime.combine(datetime.today()+timedelta(days=1),time())
		date=reported_date.isoformat()[:10]
		price=get_predicted_price(date)
		for idx, row in price.iterrows():
			new_predicted_price=PredictedPrice(
				date_time=reported_date,
				period=idx+1,
				predicted_load=row["Units(MWh)"],
				predicted_price=row["Price"]
			)
			reported_date=reported_date+timedelta(minutes=30)
			if PredictedPrice.query.get(new_predicted_price.date_time) is None:
				db.session.add(new_predicted_price)
		db.session.commit()
        
	@app.cli.command("store_bids")
	def storeBids():
		'''
		Looks up bids submitted and populates db
		'''
		reported_date=datetime.combine(datetime.today()+timedelta(days=1),time())
		date=reported_date.isoformat()[:10]
		outcome=get_bids(date)
		for idx, row in outcome.iterrows():
			new_bids=Trading(
				date_time=row["applying_date"],
				period=row["hour_ID"],
				bid_units=row["volume"],
				bid_price=row["price"],
                bid_type=row["type"],
                bid_outcome=row["accepted"]                
                
			)
			if Trading.query.get((new_bids.date_time, new_bids.period)) is None:
				db.session.add(new_bids)

		db.session.commit()
        
	@app.cli.command("make_bids")
	def makeBids():
		'''
		Post bids, this needs to run before 9 AM
		'''
		reported_date=datetime.combine(datetime.today()+timedelta(days=1),time())
		date=reported_date.isoformat()[:10]
		post_bids(date)
        
        
	@app.cli.command("clearout_prices")
	def clearoutPrice():
		'''
		Looks up clearout price
		'''
	
		clear_out=get_clearout()        
		for idx,row in clear_out.iterrows():            
			co_prices=ClearoutPrice(
				date_time=row["date"],
				period=row["period"],
				closing_price=row["price"]
            )
			if ClearoutPrice.query.get((co_prices.date_time, co_prices.period)) is None:
				db.session.add(co_prices)
		db.session.commit()
