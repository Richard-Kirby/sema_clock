import requests
import json


class TFL_Status:

    # Get setup, including reading in credentials from the JSON file.  Credentials need to be obtained from TFL.
    def __init__(self):

        # Grab the credentials.  TODO: everyone has to get their own credentials.  Not in the repo.
        with open('tfl_status/tfl_credentials.secret') as json_data_file:
            config = json.load(json_data_file)

        # assign to appropriate variables - get used for each call to get status.
        self.application_id = config['credentials']['application_id']
        self.application_keys = config['credentials']['application_keys']

        self.status_request_url = "https://api.tfl.gov.uk/Line/Mode/tube/Status?detail=false&app_key={}&app_id={}"\
            .format(config['credentials']['application_keys'], config['credentials']['application_id'])

        #print(self.status_request_url)

    def get_status(self):

        status ={}
        result= requests.get(self.status_request_url).json()
        for line in result:
            print (line['name'],":", line['lineStatuses'][0]['statusSeverityDescription'])
            status[line['name']] = line['lineStatuses'][0]['statusSeverityDescription']
        print(status)


if __name__ == "__main__":
    tfl_status = TFL_Status()
    tfl_status.get_status()

