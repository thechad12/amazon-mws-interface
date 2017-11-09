from flask import Flask, render_template, request, make_response, send_from_directory, redirect, url_for, Response, flash, session
from werkzeug.utils import secure_filename
from werkzeug.local import Local, LocalManager
from requests_toolbelt import MultipartEncoder
from models import ArrayStack
import requests
import boto
from boto.mws import connection
import boto.mws.response
import boto.mws.exception
from boto.mws.connection import MWSConnection
import os
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
import re
import json
from flask_wtf.csrf import CsrfProtect
import xml.etree.ElementTree as et
import config
from database import FeedResult, Base
import logging
from logging.handlers import RotatingFileHandler

csrf = CsrfProtect()

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['xml'])

# Keys
MWS_ACCESS_KEY = os.environ['MWS_ACCESS_KEY']
MWS_SECRET_KEY = os.environ['MWS_SECRET_KEY']
MERCHANT_ID = os.environ['MERCHANT_ID']
MARKETPLACE_ID = os.environ['MARKETPLACE_ID']


ACCOUNT_TYPE = "Merchant"

conn = connection.MWSConnection(aws_access_key_id=MWS_ACCESS_KEY,
aws_secret_access_key=MWS_SECRET_KEY, Merchant=MERCHANT_ID)

response = MWSConnection._parse_response = lambda s,x,y,z: z

engine = create_engine('sqlite:///amazon.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

data = None
stack = ArrayStack(data)

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
    elif 'inventory' in f_name:
        return '_POST_INVENTORY_AVAILABILITY_DATA_'
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
                feed_type = feed.SubmitFeedResult.FeedSubmissionId.FeedType
                date = feed.SubmitFeedResult.FeedSubmissionId.SubmittedDate
            else:
                tree = et.fromstring(feed)
                xmlns = {'response': '{http://mws.amazonaws.com/doc/2009-01-01/}'}
                info = tree.find('.//{response}FeedSubmissionId'.format(**xmlns))
                f_type = tree.find('.//{response}FeedType'.format(**xmlns))
                f_date = tree.find('.//{response}SubmittedDate'.format(**xmlns))
                feed_info = info.text
                feed_type = f_type.text
                date = f_date.text

            feed_obj = FeedResult(id=feed_info, feed_type=feed_type, date=date)
            session.add(feed_obj)
            session.commit()
            # Push feed id to stack for access
            stack.push(feed_obj.id)
            flash('Submitted Product Feed: ' + str(feed_info))
            return redirect(url_for('feed_result', feed_id=feed_info))

    else:
        return render_template('submit_feed.html',access_key=MWS_ACCESS_KEY,secret_key=MWS_SECRET_KEY,
            merchant_id=MERCHANT_ID,marketplace_id=MARKETPLACE_ID)

@app.route('/feed-history/')
def get_feeds():
    feeds = session.query(FeedResult).all()
    return render_template('feeds.html', feeds=feeds)

@app.route('/recent-feed-history/')
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
        output = '<h2>Feed processing result not ready for feed %s. Please refresh in a minute</h2>' % feed_id
        return output

