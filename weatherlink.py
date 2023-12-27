import collections
import hashlib
import hmac
import time
import datetime as dt
import json
import urllib.request
import appdaemon.plugins.hass.hassapi as hass

class WeatherlinkConditions(hass.Hass):

    """
    Example showing API Signature calculation
    for an API call to the /v2/current/{station-id}
    API endpoint
    """
    
    """
    Here is the list of parameters we will use for this example.
    """
    def initialize(self):
        self.log("Running Weatherlink!")
        kwargs = '{}'
        self.getconditions(kwargs)
#        now = dt.datetime.now()
        runtime = dt.datetime.now()
        addseconds = (round((runtime.minute*60 + runtime.second)/900)+1)*900 + 120
        self.log(runtime)
        self.log(addseconds)
        runtime = runtime.replace(minute=0, second=0, microsecond=0) + dt.timedelta(seconds=addseconds)
        self.log(runtime)
        handle = self.run_every(self.getconditions,runtime,900)
#        self.log(now)
#        t = now.time()
#        self.log(t)
#        time = dt.datetime(now.year, now.month, now.day, now.hour, (now.minute//15)*15+2)
#        self.log(time)
#        handle = self.run_every(self.getconditions, time, 900)
        pass
    
    # def getconditions(self, kwargs):
    #     parameters = {
    #               "api-key": "rnaa8nmfsl6d3lz8gtxv3ty3ykdwc1k4",
    #               "api-secret": "h6pwnbrplcreyujmowtfibousr9a6faj",
    #               "station-id": "41780", 
    #               "t": int(time.time())
    #                  }
    def getconditions(self, kwargs):
        parameters = {
                  "api-key": self.args["application_api_key"],
                  "api-secret": self.args["application_api_secret"],
                  "station-id": self.args["application_station_id"], 
                  "t": int(time.time())
                     }
        """
        Now we will compute the API Signature.
        The signature process uses HMAC SHA-256 hashing and we will
        use the API Secret as the hash secret key. That means that
        right before we calculate the API Signature we will need to
        remove the API Secret from the list of parameters given to
        the hashing algorithm.
        """
        
        """
        First we need to sort the paramters in ASCII order by the key.
        The parameter names are all in US English so basic ASCII sorting is
        safe. We will use an ordered dictionary to help keep the
        parameters sorted.
        """

        parameters = collections.OrderedDict(sorted(parameters.items()))

        """
        Let's take a moment to print out all parameters for debugging
        and educational purposes.
        """
#        for key in parameters:
#           self.log("Parameter name: \"{}\" has value \"{}\"".format(key, parameters[key]))
    
        """
        Save and remove the API Secret from the set of parameters.
        """
        apiSecret = parameters["api-secret"];
        parameters.pop("api-secret", None);
    
        """
        Iterate over the remaining sorted parameters and concatenate
        the parameter names and values into a single string.
        """
        data = ""
        for key in parameters:
           data = data + key + str(parameters[key])
    
        """
        Let's print out the data we are going to hash.
        """
#        self.log("Data string to hash is: \"{}\"".format(data))
    
        """
        Calculate the HMAC SHA-256 hash that will be used as the API Signature.
        """
        apiSignature = hmac.new(
        apiSecret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
        ).hexdigest()
        """
        Let's see what the final API Signature looks like.
        """
#        self.log("API Signature is: \"{}\"".format(apiSignature))
    
        """
        Now that the API Signature is calculated let's see what the final
        v2 API URL would look like for this scenario.
        """
        queryurl = "https://api.weatherlink.com/v2/current/{}?api-key={}&api-signature={}&t={}".format(parameters["station-id"], parameters["api-key"], apiSignature, parameters["t"])
        
#        self.log("v2 API URL: " + queryurl)
        
        with urllib.request.urlopen(queryurl) as response:
            html = response.read()
        
#        self.log(html)
        
        parsedjson = json.loads(html)
        
        for i in parsedjson:
            if type(parsedjson[i]) is list:
                for j in parsedjson[i]:
                    for k in j:
                        if type(j[k]) is list:
                            currcond = j[k]
                            data = currcond[0]
                            for l in data:
                                if l == "ts":
                                    readtime = time.ctime(data[l])
                                    self.set_state("sensor.weatherlink_readtime", state = readtime, attributes = {"friendly_name": "Weatherlink time"})
                                if l == "temp_out":
                                    self.set_state("sensor.weatherlink_temp_out", state = data[l], attributes = {"device_class": "temperature", "state_class": "measurement", "friendly_name": "Outside Temperature", "unit_of_measurement": "°F"})
                                elif l == "hum_out":
                                    self.set_state("sensor.weatherlink_hum_out", state = data[l], attributes = {"device_class": "humidity", "state_class": "measurement", "friendly_name": "Outside Humidity", "unit_of_measurement": "%"})
                                elif l == "wind_speed":
                                    self.set_state("sensor.weatherlink_wind_speed", state = data[l], attributes = {"device_class": "wind_speed", "state_class": "measurement", "friendly_name": "Wind Speed", "unit_of_measurement": "MPH"})
                                elif l == "wind_speed_10_min_avg":
                                    self.set_state("sensor.weatherlink_wind_speed_10_min_avg", state = data[l], attributes = {"device_class": "wind_speed", "state_class": "measurement", "friendly_name": "Wind Speed 10 min avg", "unit_of_measurement": "MPH"})
                                elif l == "bar":
                                    self.set_state("sensor.weatherlink_bar", state = data[l], attributes = {"device_class": "pressure", "state_class": "measurement", "friendly_name": "Barometric Pressure", "unit_of_measurement": "inHg"})
                                elif l == "wind_dir":
                                    self.set_state("sensor.weatherlink_wind_dir", state = data[l], attributes = {"friendly_name": "Wind Direction", "unit_of_measurement": "°"})
                                elif l == "bar_trend":
                                    self.set_state("sensor.weatherlink_bar_trend", state = data[l], attributes = {"device_class": "speed", "state_class": "in/h", "friendly_name": "Barometric Trend", "unit_of_measurement": "in/h"})
                                elif l == "rain_rate_clicks":
                                    if isinstance(data[l], int):
                                        rainr = data[l] / 100
                                    else:
                                        rainr = 0
                                    self.set_state("sensor.weatherlink_rain_rate_clicks", state = rainr, attributes = {"device_class": "precipitation_intensity", "state_class": "measurement", "friendly_name": "Rain Rate", "unit_of_measurement": "in/hr"})
                                elif l == "uv":
                                    self.set_state("sensor.weatherlink_uv", state = data[l], attributes = {"friendly_name": "UV Index"})
                                elif l == "solar_rad":
                                    self.set_state("sensor.weatherlink_solar_rad", state = data[l], attributes = {"device_class": "irradiance", "state_class": "measurement", "friendly_name": "Solar Radiation", "unit_of_measurement": "W/m²"})
                                elif l == "rain_storm_clicks":
                                    if isinstance(data[l], int):
                                        rains = data[l] / 100
                                    else:
                                        rains = 0
                                    self.set_state("sensor.weatherlink_rain_storm_clicks", state = rains, attributes = {"device_class": "precipitation", "state_class": "total_increasing", "friendly_name": "Rain Storm", "unit_of_measurement": "in"})
                                elif l == "rain_storm_start_date":
                                    stormtime = time.ctime(data[l])
                                    self.set_state("sensor.weatherlink_rain_storm_start_date", state = stormtime, attributes = {"friendly_name": "Rain Storm Start"})
                                elif l == "rain_day_clicks":
                                    if isinstance(data[l], int):
                                        raind = data[l] / 100
                                    else:
                                        raind = 0
                                    self.set_state("sensor.weatherlink_rain_day_clicks", state = raind, attributes = {"device_class": "precipitation", "state_class": "total_increasing", "friendly_name": "Current Day Rain", "unit_of_measurement": "in"})
                                elif l == "rain_month_clicks":
                                    if isinstance(data[l], int):
                                        rainm = data[l] / 100
                                    else:
                                        rainm = 0
                                    self.set_state("sensor.weatherlink_rain_month_clicks", state = rainm, attributes = {"device_class": "precipitation", "state_class": "total_increasing", "friendly_name": "Current Month Rain", "unit_of_measurement": "in"})
                                elif l == "rain_year_clicks":
                                    if isinstance(data[l], int):
                                        rainy = data[l] / 100
                                    else:
                                        rainy = 0
                                    self.set_state("sensor.weatherlink_rain_year_clicks", state = rainy, attributes = {"device_class": "precipitation", "state_class": "total_increasing", "friendly_name": "Current Year Rain", "unit_of_measurement": "in"})
                                elif l == "et_day":
                                    self.set_state("sensor.weatherlink_et_day", state = data[l], attributes = {"device_class": "precipitation", "state_class": "total_increasing", "friendly_name": "Current Day Evapotranspiration", "unit_of_measurement": "in"})
                                elif l == "et_month":
                                    self.set_state("sensor.weatherlink_et_month", state = data[l], attributes = {"device_class": "precipitation", "state_class": "total_increasing", "friendly_name": "Current Month Evapotranspiration", "unit_of_measurement": "in"})
                                elif l == "et_year":
                                    self.set_state("sensor.weatherlink_et_year", state = data[l], attributes = {"device_class": "precipitation", "state_class": "total_increasing", "friendly_name": "Current Year Evapotranspiration", "unit_of_measurement": "in"})
                                elif l == "dew_point":
                                    self.set_state("sensor.weatherlink_dew_point", state = data[l], attributes = {"device_class": "temperature", "state_class": "measurement", "friendly_name": "Dew Point", "unit_of_measurement": "°F"})
                                elif l == "heat_index":
                                    self.set_state("sensor.weatherlink_heat_index", state = data[l], attributes = {"device_class": "temperature", "state_class": "measurement", "friendly_name": "Heat Index", "unit_of_measurement": "°F"})
                                elif l == "wind_chill":
                                    self.set_state("sensor.weatherlink_wind_chill", state = data[l], attributes = {"device_class": "temperature", "state_class": "measurement", "friendly_name": "Wind Chill", "unit_of_measurement": "°F"})
                                elif l == "forecast_rule":
                                    self.set_state("sensor.weatherlink_forecast_rule", state = data[l], attributes = {"friendly_name": "Forecast Rule"})
                                elif l == "forecast_desc":
                                    self.set_state("sensor.weatherlink_forecast_desc", state = data[l], attributes = {"friendly_name": "Forecast Description"})
                                elif l == "wet_leaf_4":
                                    self.set_state("sensor.weatherlink_wet_leaf", state = data[l], attributes = {"device_class": "temperature", "state_class": "measurement", "Wet Leaf": "Forecast Description", "unit_of_measurement": "°F"})


        