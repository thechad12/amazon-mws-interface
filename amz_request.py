import boto
from boto.mws import connection
from boto.mws.connection import MWSConnection
from boto.mws.response import ResponseFactory, ResponseElement
from boto.handler import XmlHandler
import boto.mws.response
import itertools
import xml.etree.cElementTree as et
import time
import re

start_time = time.time()

ACCOUNT_TYPE = "Merchant"

MWS_ACCESS_KEY = 'AKIAIRVETNJ5BP5FXVQA'
MWS_SECRET_KEY = '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'
MERCHANT_ID = 'AL35W92DYBY3I'
MARKETPLACE_ID = 'ATVPDKIKX0DER'

'''Use for parsing XML file
tree = et.parse('amz-vintage-fitted-tee-check.xml')
root = tree.getroot()
xmlns = {'catalog':'{http://www.demandware.com/xml/impex/catalog/2006-10-31}'}
product = root.find('.//{catalog}product'.format(**xmlns))
IdList = []
for product in root:
    product_id = product.get('product-id')
    IdList.append(product_id)'''

'''Use for parsing plain text file'''
IdList = []
with open('amz-pr-sole-flip-flops.txt','r') as s:
    for line in s:
        n = re.split(';|,|\*\n', line)
        string = [line.strip() for i in n]
        for x in string:
            IdList.append(x)

IdType = 'SellerSKU'

# Request can only contain 5 IDs, so list needs to be split into chunks of
# 5 IDs.
def chunk(l ,n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

conn = connection.MWSConnection(aws_access_key_id=MWS_ACCESS_KEY,
            aws_secret_access_key=MWS_SECRET_KEY, Merchant=MERCHANT_ID)
counter = 0
for ids in chunk(IdList, 5):
        response = MWSConnection._parse_response = lambda s,x,y,z: z
        skus = conn.get_matching_product_for_id(MarketplaceId=MARKETPLACE_ID, IdList=ids,
            IdType=IdType)
        print skus
        # Amazon can only handle 18,000 requests per hour of this type
        counter += 1
        current_time = (time.time() - start_time)
        if counter == 18000 and time <= 3600:
            remaining_time = (3600 - current_time)
            time.sleep(remaining_time)

print("----%s seconds ----" % (time.time() - start_time))

conn.close()
