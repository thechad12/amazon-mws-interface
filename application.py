from flask import Flask, render_template, request, make_response, send_from_directory, redirect, url_for, Response, flash, session
from werkzeug.utils import secure_filename
from werkzeug.local import Local, LocalManager
from requests_toolbelt import MultipartEncoder
import requests
import boto
from boto.mws import connection
import boto.mws.response
import boto.mws.exception
from boto.mws.connection import MWSConnection
import itertools
import os
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
import re
import json
import httplib2
from flask_wtf.csrf import CsrfProtect
import xml.etree.ElementTree as et


csrf = CsrfProtect()

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['xml'])

# Keys
MWS_ACCESS_KEY = json.loads(open(
    'amazon.json','r').read())['web']['access_key']
MWS_SECRET_KEY = json.loads(open(
    'amazon.json','r').read())['web']['secret_key']
MERCHANT_ID = json.loads(open(
    'amazon.json','r').read())['web']['merchant_id']
MARKETPLACE_ID = json.loads(open(
    'amazon.json','r').read())['web']['marketplace_id']

ACCOUNT_TYPE = "Merchant"

conn = connection.MWSConnection(aws_access_key_id=MWS_ACCESS_KEY,
aws_secret_access_key=MWS_SECRET_KEY, Merchant=MERCHANT_ID)

response = MWSConnection._parse_response = lambda s,x,y,z: z

@app.route('/')
@app.route('/home/')
def home():
    return render_template('home.html')

# Call out allowed file types
def allowed_filetype(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Function to call correct operation type for submitting xml feed
def feed_operation(f_name):
    if 'pricing' in f_name or 'price' in f_name:
        return '_POST_PRODUCT_PRICING_DATA_'
    elif 'relationship' in f_name or 'connection' in f_name or 'relation' in f_name:
        return '_POST_PRODUCT_RELATIONSHIP_DATA_'
    elif 'image' in f_name:
        return '_POST_PRODUCT_IMAGE_DATA_'
    elif 'product' in f_name:
        return '_POST_PRODUCT_DATA_'
    else:
        raise ValueError('Please name your file appropriately')


# Submit feed to amazon
@app.route('/submission/', methods=['GET','POST'])
def feed_submission():
    if request.method == 'POST':
            file = request.files['file']

            # Only XML files allowed
            if not allowed_filetype(file.filename):
                output = '<h2 style="color:red">Filetype must be XML! Please upload an XML file.</h2>'
                return output
                raise ValueError('Filetype Must Be XML.')

            # Read file and encode it for transfer to Amazon
            file_name = request.form['file_name']
            f = file.read()
            u = f.decode("utf-8-sig")
            c = u.encode("utf-8")
            feed_content = c

            feed = conn.submit_feed(
                FeedType=feed_operation(file_name),
                PurgeAndReplace=False,
                MarketplaceIdList=[MARKETPLACE_ID],
                content_type='text/xml',
                FeedContent=feed_content)

            if type(feed) is not str:
                feed_info = feed.SubmitFeedResult.FeedSubmissionInfo.FeedSubmissionId
            else:
                tree = et.fromstring(feed)
                xmlns = {'response': '{http://mws.amazonaws.com/doc/2009-01-01/}'}
                info = tree.find('.//{response}FeedSubmissionId'.format(**xmlns))
                feed_info = info.text

            flash('Submitted Product Feed: ' + str(feed_info))
            return redirect(url_for('feed_result', feed_id=feed_info))

    else:
        return render_template('submit_feed.html',access_key=MWS_ACCESS_KEY,secret_key=MWS_SECRET_KEY,
            merchant_id=MERCHANT_ID,marketplace_id=MARKETPLACE_ID)

@app.route('/feed-history')
def feed_history():
    feed_history = conn.get_feed_submission_list()
    response = Response(feed_history, mimetype='text/xml')
    return response

@csrf.error_handler
def csrf_error(error):
    return render_template('csrf_error.html', error=error), 400

# Retrieve submitted feed result
@app.route('/feed-result/<int:feed_id>')
def feed_result(feed_id):
    try:
        submitted_feed = conn.get_feed_submission_result(FeedSubmissionId=feed_id)

        response = Response(submitted_feed, mimetype='text/xml')
        return response
    except:
        output = '<h2>Feed processing result not ready. Please refresh in a minute</h2>'
        return output

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'secret_key'
    app.run(host='0.0.0.0', port=8000)
