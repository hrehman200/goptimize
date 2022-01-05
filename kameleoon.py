import requests
import pandas as pd
import pygsheets

CLIENT_ID = 'xxx'
CLIENT_SECRET = 'xxx'

data = []

response = requests.post(
    'https://api.kameleoon.com/oauth/token',
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    },
    data={
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
)
json_response = response.json()

token = json_response['access_token']

print(token)

response = requests.get(
    'https://api.kameleoon.com/experiments',
    headers={
        "Authorization": 'Bearer '+token,
        "Content-Type": "application/json"
    },
    data={
        # 'page': 1,
        # 'perpage': 10,
        'filter': '[{"field":"status","operator":"EQUAL","parameters":["FINISHED"]}]'
    }
)
print(response)
json_response = response.json()

def condition(dic):
    return dic['name'] == 'GOOGLE_UNIVERSAL_ANALYTICS'

for row in json_response:
    if(len(row['schedules']) > 0 and 'dateStart' in row['schedules'][0]):
        print(row['schedules'])
        item = {
            'Kameleoon Test ID': row['id'],
            'Test Name': row['name'],
            'Custom Dimension': row['trackingTools'][0]['universalAnalyticsDimension'],
            'Start Date': row['schedules'][0]['dateStart'],
            'End Date': row['schedules'][0]['dateEnd'],
            'Site ID': row['siteId'],
            'Domain': row['baseURL']
        }

        response = requests.get(
            'https://api.kameleoon.com/sites/'+str(row['siteId'])+'/integration-tools',
            headers={
                "Authorization": 'Bearer '+token,
                "Content-Type": "application/json"
            }
        )
        response= response.json()
        print(response)

        filtered = [d for d in response if condition(d)]

        if len(filtered) > 0 and 'trackingId' in filtered[0]['settings']:
            item['Google Analytics View ID'] = filtered[0]['settings']['trackingId']

        data.append(item)

gc = pygsheets.authorize(
service_file='./startandenddateautomation-494e73c92522.json')
df = pd.DataFrame(data)
sh = gc.open('Kameleoon Sheet')
wks = sh[0]
wks.set_dataframe(df, (1, 1))
