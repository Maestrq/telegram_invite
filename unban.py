import pymongo
from dotenv import load_dotenv
import os
load_dotenv()
myclient = pymongo.MongoClient(os.getenv("MONGO_STRING"))
mydb = myclient["inviting"]
accounts = mydb["accounts"]
import time


while True:
    suspended_accounts = accounts.find({"Suspended" : True})
    for account in suspended_accounts:
        if time.time() > account['unban_time']:
            accounts.update_one({'_id' : account['_id']}, {"$set" : {'Suspended' : False}})
    time.slepp(5)