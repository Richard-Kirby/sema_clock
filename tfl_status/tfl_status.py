import requests
import json
import threading
import time


# Class that manages the TFL status - sorts out the credentials and makes the queries when asked.
class TFL_Status(threading.Thread):

    # Get setup, including reading in credentials from the JSON file.  Credentials need to be obtained from TFL.
    def __init__(self):
        # Init the threading
        threading.Thread.__init__(self)

        # Grab the credentials.  TODO: everyone has to get their own credentials.  Not in the repo.
        with open('tfl_status/tfl_credentials.secret') as json_data_file:
            config = json.load(json_data_file)

        # assign to appropriate variables - get used for each call to get status.
        self.application_id = config['credentials']['application_id']
        self.application_keys = config['credentials']['application_keys']

        self.status_request_url = "https://api.tfl.gov.uk/Line/Mode/tube/Status?detail=false&app_key={}&app_id={}"\
                .format(config['credentials']['application_keys'], config['credentials']['application_id'])

        self.status_dictionary = None

        #print(self.status_request_url)

    # Get the status from the TFL site and process it to get just the summary status.
    def get_summary_status(self):

        status ={}

        try:
            print("trying")
            result= requests.get(self.status_request_url).json()
            for line in result:
                print (line['name'],":", line['lineStatuses'][0]['statusSeverityDescription'])
                status[line['name']] = line['lineStatuses'][0]['statusSeverityDescription']
        except:
            print("tfl status get failed - random number generator or Internet not avail?")
            #raise

        #print(status)
        return status

    def run(self):

        # Get the status every once in a while
        while True:
            self.status_dictionary = self.get_summary_status()
            time.sleep(60)



if __name__ == "__main__":
    tfl_status = TFL_Status()
    tfl_status.get_summary_status()
    tfl_status.start()
