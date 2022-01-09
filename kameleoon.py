import requests
import pandas as pd
import pygsheets
import sys
import json
import datetime

CLIENT_ID = 'xxx'
CLIENT_SECRET = 'xxx'

args = sys.argv
# stopped or paused
STATUS_TO_FETCH = args[1]

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


def condition(dic):
    return dic['name'] == 'GOOGLE_UNIVERSAL_ANALYTICS'


# Also for the start and end date please remove the timestamps, only put in the actual date like: 4/27/2020
def dt_format(timestamp):
    if timestamp == '':
        return ''
    timestamp = timestamp.split('T')[0]
    dt = datetime.datetime.strptime(timestamp, '%Y-%m-%d')
    return '{0}/{1}/{2:02}'.format(dt.month, dt.day, dt.year % 100)


for page in range(1, 2):
    response = requests.get(
        'https://api.kameleoon.com/experiments',
        headers={
            "Authorization": 'Bearer '+token,
            "Content-Type": "application/json"
        },
        params={
            'page': page,
            'perPage': 200,  # maximum per page 200
            'filter': '[{"field":"status","operator":"EQUAL","parameters":["'+STATUS_TO_FETCH+'"]}]'
        }
    )
    json_response = response.json()

    print(page)

    with open("out.log", "w", encoding="utf-8") as f:
        f.write(json.dumps(json_response))

    for row in json_response:

        # For Kameleoon Experiments please filter out experiments that do not have a dimension associated
        if len(row['trackingTools']) == 0 or 'universalAnalyticsDimension' not in row['trackingTools'][0]:
            continue

        item = {
            'Kameleoon Test ID': row['id'],
            'Test Name': row['name'],
            'Custom Dimension': row['trackingTools'][0]['universalAnalyticsDimension'],
            # 'Start Date': row['schedules'][0]['dateStart'] if len(row['schedules']) > 0 and 'dateStart' in row['schedules'][0] else '',
            # 'End Date': row['schedules'][0]['dateEnd'] if len(row['schedules']) > 0 and 'dateEnd' in row['schedules'][0] else '',
            'Start Date': dt_format(row['dateStarted']),
            'End Date': dt_format(row['dateEnded'] if 'dateEnded' in row else ''),
            'Site ID': row['siteId'],
            'Domain': row['baseURL'] if 'baseURL' in row else ''
        }

        response = requests.get(
            'https://api.kameleoon.com/sites/' +
            str(row['siteId'])+'/integration-tools',
            headers={
                "Authorization": 'Bearer '+token,
                "Content-Type": "application/json"
            }
        )
        response = response.json()

        filtered = [d for d in response if condition(d)]

        if len(filtered) > 0 and 'trackingId' in filtered[0]['settings']:
            item['Google Analytics View ID'] = filtered[0]['settings']['trackingId']

        print(item)
        data.append(item)

gc = pygsheets.authorize(
    service_file='./startandenddateautomation-494e73c92522.json')
df = pd.DataFrame(data)
sh = gc.open('Kameleoon Sheet')
if STATUS_TO_FETCH == 'stopped':
    wks = sh[0]
elif STATUS_TO_FETCH == 'paused':
    wks = sh[1]
wks.set_dataframe(df, (1, 1))
