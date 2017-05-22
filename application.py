from flask import Flask, render_template, request, make_response, send_from_directory, redirect, url_for, Response, flash
from werkzeug.utils import secure_filename
from requests_toolbelt import MultipartEncoder
import requests
import boto
from boto.mws import connection
from boto.mws.connection import MWSConnection
import itertools
import os
import gc
import json
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database import Base, FeedResult
from flask_wtf.csrf import CsrfProtect


csrf = CsrfProtect()

engine = create_engine('sqlite:///amazon.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['xml'])
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DOWNLOAD_FOLDER = 'downloads/'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
FEED_FOLDER = 'feeds/'
app.config['FEED_FOLDER'] = FEED_FOLDER

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
            submit_feed_response = conn.submit_feed(
                FeedType=feed_operation(file_name),
                PurgeAndReplace=False,
                MarketplaceIdList=[MARKETPLACE_ID],
                content_type='text/xml',
                FeedContent=feed_content)
            feed_info = submit_feed_response.SubmitFeedResult.FeedSubmissionInfo.FeedSubmissionId
            return redirect(url_for('feed_result', feed_id=feed_info))
    else:
        return render_template('submit_feed.html',access_key=MWS_ACCESS_KEY,secret_key=MWS_SECRET_KEY,
            merchant_id=MERCHANT_ID,marketplace_id=MARKETPLACE_ID)


@csrf.error_handler
def csrf_error(error):
    return render_template('csrf_error.html', error=error), 400

# Retrieve submitted feed result
@app.route('/feed-result/<int:feed_id>')
def feed_result(feed_id):
    response = MWSConnection._parse_response = lambda s,x,y,z: z
    submitted_feed = conn.get_feed_submission_result(FeedSubmissionId=feed_id)
    result = Response(submitted_feed, mimetype='text/xml')
    return(result)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'secret_key'
    app.run(host='0.0.0.0', port=8000)
