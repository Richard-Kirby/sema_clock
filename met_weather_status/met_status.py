import requests
import json
import threading
import time

weather_types =[
    "Clear night",
    "Sunny day",
    "Partly cloudy (night)",
    "Partly cloudy (day)",
    "Not used",
    "Mist",
    "Fog",
    "Cloudy",
    "Overcast",
    "Light rain shower (night)",
    "Light rain shower (day)"
    "Drizzle"
    "Light rain"
    "Heavy rain shower (night)",
    "Heavy rain shower (day)",
    "Heavy rain",
    "Sleet shower (night)",
    "Sleet shower (day)",
    "Sleet",
    "Hail shower (night)",
    "Hail shower (day)",
    "Hail",
    "Light snow shower (night)",
    "Light snow shower (day)",
    "Light snow",
    "Heavy snow shower (night)",
    "Heavy snow shower (day)",
    "Heavy snow",
    "Thunder shower (night)",
    "Thunder shower (day)",
    "Thunder"]

# Class that manages the TFL status - sorts out the credentials and makes the queries when asked.
class MetWeatherStatus(threading.Thread):

    # Get setup, including reading in credentials from the JSON file.  Credentials need to be obtained from TFL.
    def __init__(self):
        # Init the threading
        threading.Thread.__init__(self)

        # Grab the credentials.  TODO: everyone has to get their own credentials.  Not in the repo.
        with open('met_weather_status/met_credentials.secret') as json_data_file:
            config = json.load(json_data_file)

        # assign to appropriate variables - get used for each call to get status.
        self.application_key = config['credentials']['application_key']

        self.status_request_url = "http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/324151?res=daily&key={}"\
            .format(self.application_key)

        self.status_dictionary = None
        print(self.status_request_url)

    # Get the status from the TFL site and process it to get just the summary status.
    def get_summary_status(self):

        status ={}

        try:
            print("trying")
            result= requests.get(self.status_request_url).json()
            #print(result)
            print(result["SiteRep"]["DV"]["Location"]["name"])

            i = 0
            five_day_forecast = []

            for day in result["SiteRep"]["DV"]["Location"]["Period"]:
                day_forecast = day["Rep"].pop(0)
                night_forecast = day["Rep"].pop(0)

                simple_day_forecast = {"day_weather_type": weather_types[int(day_forecast["W"])],
                                       "night_weather_type": weather_types[int(night_forecast["W"])],
                                       "high_temp": day_forecast["Dm"],
                                       "low_temp": night_forecast["Nm"]}


                five_day_forecast.append(simple_day_forecast)

            for i in range(len(five_day_forecast)):
                print(i, five_day_forecast[i])

        except:
            print("tfl status get failed - random number generator or Internet not avail?")
            raise

        #print(status)
        return status

    def run(self):
        # trying to ensure there is enough entropy to get started.  Just wait for 5 min.  Could be more clever.
        #time.sleep(300)

        # Get the status every once in a while
        while True:
            self.status_dictionary = self.get_summary_status()
            time.sleep(120)



if __name__ == "__main__":
    met_weather_status = MetWeatherStatus()
    met_weather_status.get_summary_status()
    met_weather_status.start()

