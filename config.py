import os
import json

os.environ['MWS_ACCESS_KEY'] = json.loads(open(
    'amazon.json','r').read())['web']['access_key']
os.environ['MWS_SECRET_KEY'] = json.loads(open(
    'amazon.json','r').read())['web']['secret_key']
os.environ['MERCHANT_ID'] = json.loads(open(
    'amazon.json','r').read())['web']['merchant_id']
os.environ['MARKETPLACE_ID'] = json.loads(open(
    'amazon.json','r').read())['web']['marketplace_id']
os.environ['secret_key'] = json.loads(open('config.json', 'r').read())['app']['secret_key']
os.environ['host'] = '0.0.0.0'
os.environ['port'] = '8000'
