from flask import Flask, jsonify
from app import app
from user.models import User
import pymongo
from passlib.hash import pbkdf2_sha256

from flask import render_template, session, redirect, request
from functools import wraps
from bson.objectid import ObjectId
from flask import Flask, render_template, session, redirect, request,url_for,jsonify,make_response

client = pymongo.MongoClient('localhost', 27017)
db = client.mydatabase
collection = db['invoices']





@app.route('/user/signup', methods=['POST'])
def signup():
    return User().signup()





# @app.route('/user/signout')
# def signout():
#     return User().signout()


# @app.route('/invoices')
# def invoices():
#     invoices = list(db.invoices.find({}))
#     for invoice in invoices:
#         invoice['_id'] = str(invoice['_id'])
#     return jsonify(invoices)
########## Imp##########

# import jwt
# import datetime
# @app.route('/user/login', methods=['GET','POST'])
# def user_login():
#     if request.method =='GET':
#         return render_template('login.html')
#     else:
#         email = request.form.get('email')
#         password = request.form.get('password')
#         # Find user with matching email in the database
#         user = db.users.find_one({ "email": email })
#         # Check if the user exists and the password is correct
#         if user and pbkdf2_sha256.verify(password, user['password']):
#             # Generate a JWT token
#             payload = {
#                 'user_id': str(user['_id']),
#                 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
#             }
#             token = jwt.encode(payload, 'secret_key', algorithm='HS256')

#             result = {'token':token}
#             # Return the token as a JSON response
#             return jsonify(result)

#         # Return error message if login fails
#         return jsonify({ "error": "Invalid login credentials" }), 401
############################

import jwt
import datetime

result = ''

# @app.route('/user/login', methods=['GET','POST'])
# def user_login():
#     if request.method =='GET':
#         return render_template('login.html')
#     else:
#         email = request.form.get('email')
#         password = request.form.get('password')
#         # Find user with matching email in the database
#         user = db.users.find_one({ "email": email })
#         # Check if the user exists and the password is correct
#         if user and pbkdf2_sha256.verify(password, user['password']):
#             session['logged_in'] = True
#             # Generate a JWT token with user ID in payload
#             payload = {
#                 'user_id': str(user['_id']),
#                 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
#             }
#             token = jwt.encode(payload, 'secret_key', algorithm='HS256')

#             result = {'token':token}
#             # Return the token as a JSON response
#             return jsonify(result)

#         # Return error message if login fails
#         return jsonify({ "error": "Invalid login credentials" }), 401

# @app.route('/invoices')
# def invoices():
#     # Check if a valid JWT token is present in the request headers
#     token = request.headers.get('Authorization')
#     if not token:
#         return jsonify({ "error": "Missing authorization token" }), 401

#     try:
#         # Decode the token and extract the user ID from the payload
#         payload = jwt.decode(token, 'secret_key', algorithms=['HS256'])
#         user_id = payload['user_id']
#     except:
#         return jsonify({ "error": "Invalid authorization token" }), 401

#     # Query the database for invoices belonging to the user
#     invoices = list(db.invoices.find({ "user": user_id }))
#     for invoice in invoices:
#         invoice['_id'] = str(invoice['_id'])
#     return jsonify(invoices)


# @app.route('/user/forgot_password', methods=['GET', 'POST'])
# def forgot_password():
#     if request.method == 'GET':
#         return render_template('forgot_password.html')
#     else:
#         email = request.form.get('email')
#         user = db.users.find_one({ "email": email })

#         if user:
#             # generate a new random password
        #     import random
        #     import string
        #     new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

        #     # update user's password in the database
        #     hashed_password = pbkdf2_sha256.encrypt(new_password, rounds=200000, salt_size=16)
        #     db.users.update_one({"_id": user["_id"]}, {"$set": {"password": hashed_password}})

        #     # send the new password to the user via email
        #     # code to send email goes here

        #     return render_template('forgot_password_success.html')
        # else:
        #     return render_template('forgot_password.html', error='Invalid email address')
