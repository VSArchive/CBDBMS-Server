from email import message
import os
from datetime import datetime
from random import randint

import smtplib
from dotenv import load_dotenv
from pymongo import MongoClient
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask

load_dotenv()

# connect to DB
client = MongoClient(os.getenv("MONGODB"))

# DB references
db = client.cbdbms
parent_db = db.parent
child_db = db.child
transaction_db = db.transaction
transaction_request_db = db.transaction_request

app = Flask(__name__)


# Child transaction
def approve_child_transaction(transaction_request_id):
    try:
        transaction_request = transaction_request_db.find_one(
            {"transaction_request_id": transaction_request_id})

        child_details = child_db.find_one(
            {"username": transaction_request["child_username"], "account_number": transaction_request["child_account_number"]})
        balance_update = {"$set": {"balance": int(
            child_details["balance"]) - transaction_request["amount"]}}
        child_db.update_one(
            {"username": transaction_request["child_username"], "account_number": transaction_request["child_account_number"]}, balance_update)

        transaction_db.create_index("transaction_id", unique=True)
        transaction_details = {
            "username": transaction_request["child_username"],
            "transaction_id": randint(1, 1000000000000),
            "transactionAt": datetime.now(),
            "amount": transaction_request["amount"],
            "from_account_number": transaction_request["child_account_number"],
            "to_account_number": transaction_request["toAcc"],
            "by_type": "child",
            "to_type": "child",
            "transaction_type": "1to1",
            "approved_by": transaction_request["parent_account_number"],
            "message": "Approved by parent via link"
        }
        transaction_db.insert_one(transaction_details)

        child_details = child_db.find_one(
            {"account_number": transaction_request["toAcc"]})
        if bool(child_details):
            balance_update = {
                "$set": {"balance": child_details["balance"] + transaction_request["amount"]}}
            child_db.update_one(
                {"username": child_details["username"], "account_number": transaction_request["toAcc"]}, balance_update)

            transaction_request_db.delete_one(
                {"transaction_request_id": int(transaction_request_id)})
            return True, "transaction success"
        else:
            return False, "account dose not exist"

    except Exception as e:
        print(e)
        return False, e


@app.route("/")
def hello_world():
    return "<p>API is Running</p>"


@app.route("/approve/<int:id>")
def approve(id):
    success, _ = approve_child_transaction(id)
    if success:
        return "<p>Transaction Approved Successfully: {}</p>".format(id)
    else:
        return "<p>Transaction Already Approved or dose not exists: {}</p>".format(id)


if __name__ == "__main__":
    app.run()
