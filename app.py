from flask import Flask, render_template, session, redirect, request,url_for,jsonify,make_response
from functools import wraps
import pymongo
import uuid
import smtplib
from flask_mail import Mail, Message
from passlib.hash import pbkdf2_sha256
import os
from image_processing.services import ImageEnhancer
import sys
import cv2
import pytesseract
from pytesseract import Output
import pandas as pd
from PIL import Image
import os
from werkzeug.utils import secure_filename
import cv2
import pandas as pd
from PIL import Image
import os
from pymongo import MongoClient
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from bson.json_util import loads, dumps
from bson.objectid import ObjectId
from flask_cors import CORS

import numpy as np
import sys
import os
from pdf2image import convert_from_path

from routes import *
from bson import ObjectId
import numpy as np
import sys
import os
from pdf2image import convert_from_path
import jwt
import datetime
from flask_login import current_user
from flask import flash
from datetime import timedelta

from bson.binary import Binary
from PIL import Image

class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(MyEncoder, self).default(obj)

app = Flask(__name__,template_folder='templates')
CORS(app)

#app.secret_key = b'\xcc^\x91\xea\x17-\xd0W\x03\xa7\xf8J0\xac8\xc5'
app.secret_key = 'secret_key'

# Database
client = pymongo.MongoClient('localhost', 27017)
#db = client.user_login_system
db = client.mydatabase
collection = db['invoices']



# Decorators
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')
    return wrap

# Routes
@app.route('/delete-invoice-<id>')
@login_required

def deleteInvoice(id):
    print(id)
    collection.delete_one({"_id":ObjectId(id)})
    return redirect(url_for("data"))

@app.route('/update-invoice-<id>', methods=['GET'])
@login_required

def get_invoice(id):
    # Retrieve the invoice document from the database
    invoice = collection.find_one({'_id': ObjectId(id)})

    # Replace any None value with an empty string in the invoice object

    # Render the update invoice template with the invoice data
    return render_template('update_invoice.html', invoice=invoice)

from datetime import datetime

@app.route('/update-invoice-<id>', methods=['POST'])
@login_required

def update_invoice(id):
    # Get the updated invoice data from the form
    invoice_data = {
        'invoice_date': request.form['invoice_date'],
        'invoice_due_date': request.form['invoice_due_date'],
        'invoice_number': request.form['invoice_number'],
        'order_from': request.form['order_from'],
        'company_address': request.form['company_address'],
        'contact_no': request.form['contact_no'],
        'Bill_to': request.form['Bill_to'],
        'name': request.form['name'],
        'shipping_address': request.form['shipping_address'],
        'phone': request.form['phone'],
        'email': request.form['email'],
        # 'items': request.form['items'],

        'Currency': request.form['Currency'],
        'Subtotal': float(request.form['Subtotal']),
        'Shipping': float(request.form['Shipping']),
        'Tax': float(request.form['Tax']),
        'Total': float(request.form['Total']),
        'ABN': request.form['ABN'],
        'Rego': request.form['Rego'],

        'Make': request.form['Make'],
        'Model': request.form['Model']
    }

    # Check if the Odometer value is not empty before converting to float
    if request.form['Odometer']:
        invoice_data['Odometer'] = float(request.form['Odometer'])
    else:
        invoice_data['Odometer'] = 'null'

    if 'items' in request.form:
        invoice_data['items'] = request.form.get('items')

    # Convert invoice_date to a datetime object if it's not empty
    if invoice_data['invoice_date']:
        invoice_data['invoice_date'] = datetime.fromisoformat(invoice_data['invoice_date'])
    # Convert invoice_due_date to a datetime object if it's not empty
    if invoice_data['invoice_due_date']:
        invoice_data['invoice_due_date'] = datetime.fromisoformat(invoice_data['invoice_due_date'])
    
    # Update the invoice document in the database
    collection.update_one({'_id': ObjectId(id)}, {'$set': invoice_data})

    # Redirect to the updated invoice page
    return redirect(url_for('data', id=id))

@app.route('/update-items/<invoice_id>', methods=['GET', 'POST'])
@login_required

def update_items(invoice_id):
    print(f"invoid===", invoice_id)
    invoice = collection.find_one({'_id': ObjectId(invoice_id)})
    if request.method == 'POST':
        # update items in the database
        items = []
        for i in range(len(request.form.getlist('qty'))):
            item = {
                'qty': int(request.form.getlist('qty')[i]),
                'unt_pr': float(request.form.getlist('unit_price')[i]),
                'product': request.form.getlist('product')[i],
            }
            items.append(item)
        collection.update_one({'_id': ObjectId(invoice_id)}, {'$set': {'items': items}})

        # redirect to hello page with updated invoice ID
        return redirect(url_for('update_invoice', id=invoice_id))
    # img_path = "Logo"
    return render_template('update_items.html', items=invoice['items'], invoice_id=invoice_id)
@app.route('/')
def home():
    return render_template('home.html')

r={}
user_id = None  # define user_id globally

@app.route('/user/login', methods=['GET','POST'])
def user_login():
    global user_id  # use the global variable
    if request.method =='GET':
        return render_template('login.html')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        # Find user with matching email in the database
        user = db.users.find_one({ "email": email })

        # Check if the user exists and the password is correct
        if user and pbkdf2_sha256.verify(password, user['password']):
            session['logged_in'] = True

            # Check if the user has a token in their database record
            if 'token' in user and 'token_expiration' in user:
                # Check if the token has expired
                if user['token_expiration'] > datetime.utcnow():
                    # Use the existing token
                    token = user['token']
                else:
                    # Generate a new token and update the user's database record
                    payload = {
                        'user_id': str(user['_id']),
                        'email': user['email'],
                        'exp': datetime.utcnow() + timedelta(days=10)
                    }
                    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
                    db.users.update_one({'_id': user['_id']}, {'$set': {'token': token, 'token_expiration': payload['exp']}})
            else:
                # Generate a new token and store it in the user's database record
                payload = {
                    'user_id': str(user['_id']),
                    'email': user['email'],
                    'exp': datetime.utcnow() + timedelta(days=10)
                }
                token = jwt.encode(payload, app.secret_key, algorithm='HS256')
                db.users.update_one({'_id': user['_id']}, {'$set': {'token': token, 'token_expiration': payload['exp']}})

            r = {'token': token}
            decoded_token = jwt.decode(r['token'], 'secret_key', algorithms=['HS256'])
            user_id = decoded_token['user_id']
            print(user_id)
            email = decoded_token['email']
            print(email)
            # Return the token as a JSON response
            return jsonify(r)

        # Return error message if login fails
        return jsonify({ "error": "Invalid login credentials" }), 401
    

@app.route('/invoices')
def invoices():
    global user_id
    # Check if a valid JWT token is present in the request headers
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({ "error": "Missing authorization token" }), 401

    try:
        # Decode the token and extract the user ID from the payload
        secret_key = 'secret_key'
        algorithm = 'HS256'

        payload = jwt.decode(token, secret_key, algorithms=[algorithm])

        user = db.users.find_one({"email": payload['email']})
        user_id = ObjectId( user['_id'])

    except Exception as e:
        print(e)
        return jsonify({ "error": "Invalid authorization token" }), 401

    # Query the database for invoices belonging to the user
    invoices = json.loads(dumps(db.invoices.find({"user_id": ObjectId(user_id)})))


    return invoices
    # Return invoices as JSON
    # return jsonify({ "invoices": invoices })

app.config["UPLOAD_FOLDER"] = "uploads/documents"

@app.route('/wrong/')
@login_required
def wrong():
    return render_template('wrong.html')



@app.route('/dashboard/', methods=["GET", "POST"])
@login_required
def dash():

     
    if request.method == "GET" :
        # print("inside dasbhord", user_id )
        return render_template('dashboard.html')

    elif request.method == "POST":
        if request.files:
            pdf=request.files["pdf"]
            

            # generate a unique identifier for the folder and file names
            unique_id = str(uuid.uuid4())
            folder_name = unique_id
            file_name = "doc_" + unique_id + ".pdf"

            folder_path = os.path.join(app.config["UPLOAD_FOLDER"], folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            pdf.save(os.path.join(folder_path, file_name))

            # set the file path for later use
            file_path = folder_name

            # continue with image and thumbnail generation
            source_dir = os.getcwd() + '/uploads/documents/'

            # create directories for images and thumbnails
            dest_img_dir = source_dir + file_path + "/images/"
            thumbnail_dir = source_dir + file_path + "/thumbnails/"
            if not os.path.exists(dest_img_dir):
                os.makedirs(dest_img_dir)
            if not os.path.exists(thumbnail_dir):
                os.makedirs(thumbnail_dir)

            # call the function to generate images and thumbnails
            ImageEnhancer.convert_pdf_to_image(source_dir + file_path + "/" + file_name, dest_img_dir, thumbnail_dir)

                    ######## Code for opening multiple images from folder and merging it vertically###########
            from PIL import Image

            # List of image filenames
            path=source_dir + file_path+"/images/"
            #path=source_dir+file_path+"/images/"
            image_filenames = os.listdir(path)

            # Open the images
            images = [Image.open(os.path.join(path, filename)) for filename in image_filenames]

            # Get the widths and heights of the images
            widths = [image.width for image in images]
            heights = [image.height for image in images]

            # Calculate the new width and height of the merged image
            new_width = max(widths)
            new_height = sum(heights)

            # Create a new image with the desired size
            merged_image = Image.new("RGB", (new_width, new_height))

            # Paste the images into the merged image, one below the other
            y_offset = 0
            for image in images:
                merged_image.paste(image, (0, y_offset))
                y_offset += image.height

            # Save the merged image
            merged_image.save(os.path.join(folder_path, "merged_image.jpg"))
            #folder_path1 = "uploads/documents"+file_path
            folder_path1 = f"uploads\documents\{file_path}"



# Get a list of all files in the folder
          ######### ##############
            file_list = os.listdir(folder_path1)
            print(file_list)
            merged_image_list = [filename for filename in file_list if filename == "merged_image.jpg"]

            for merged_image_filename in merged_image_list:
                    merged_image_path = os.path.join(folder_path1, merged_image_filename)

# # ###############     ###################
           
                # Perform the desired operation on the merged image in the current folder
                    img = cv2.imread(merged_image_path)
                   
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                    custom_config = r'-l eng --oem 1 --psm 6 '
                    d = pytesseract.image_to_data(thresh, config=custom_config, output_type=Output.DICT)
                    df = pd.DataFrame(d)

                    df1 = df[(df.conf != '-1') & (df.text != ' ') & (df.text != '')]
                    pd.set_option('display.max_rows', None)
                    pd.set_option('display.max_columns', None)

                    sorted_blocks = df1.groupby('block_num').first().sort_values('top').index.tolist()
                    for block in sorted_blocks:
                        curr = df1[df1['block_num'] == block]
                        sel = curr[curr.text.str.len() > 3]
                        # sel = curr
                        char_w = (sel.width / sel.text.str.len()).mean()
                        prev_par, prev_line, prev_left = 0, 0, 0
                        text = ''
                        for ix, ln in curr.iterrows():
                            # add new line when necessary
                            if prev_par != ln['par_num']:
                                text += '\n'
                                prev_par = ln['par_num']
                                prev_line = ln['line_num']
                                prev_left = 0
                            elif prev_line != ln['line_num']:
                                text += '\n'
                                prev_line = ln['line_num']
                                prev_left = 0

                            added = 0  # num of spaces that should be added
                            if ln['left'] / char_w > prev_left + 1:
                                added = int((ln['left']) / char_w) - prev_left
                                text += ' ' * added
                            text += ln['text'] + ' '
                            prev_left += len(ln['text']) + added + 1
                        text += '\n'
                        print(text)
                        ###########
                        if "Your_Company_name" in text:
                            import re
                            # match1=re.findall(r'Your_Company_name:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            regex12=re.compile(r"Your_Company_name[^:]*:\s*([\w\s,\\.\-\/\&]+?)(?=[\r\n]+\s*Your_address)")
                            match1=regex12.search(text)
                            # match2=re.findall(r'Your_address:(\d+)\s+([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\-\d+\s+\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\-\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\\\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)',text)
                            regex=re.compile(r"Your_address[^:]*:\s*([\w\s,\\.\-\/\&]+?)(?=[\r\n]+\s*Enter)")
                            match2 = regex.search(text)

                            # match3=re.findall(r'BILL_TO:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            regex3=re.compile(r"BILL_TO[^:]*:\s*([\w\s,\\.\-\/\&]+?)(?=[\r\n]+\s*Address)")
                            match3=regex3.search(text)
                            match4=re.findall(r'Invoice_number:(\s+(\w+)|(\w+))',text)
                            match5=re.findall(r'\d+[/.-]\d+[/.-]\d+',text)
                            match6=re.findall(r'City:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            match7=re.findall(r'Country:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            match8=re.findall(r'Postal:((\s+\w+)|\w+)',text)
                            match9=re.findall(r'SUB_TOTAL:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match10=re.findall(r'SHIPPING:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match11=re.findall(r'TAX:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            #match11=re.findall(r'TAX:(\s*([\d,]+))',text)

                            match12=re.findall(r'GRAND_TOTAL:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            # match13=re.findall(r'Address:(([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+)|([\w\s]+),([\w\s]+),([\w\s]+)|([\w\s]+),([\w\s]+)|([\w\s]+))',text)
                            regex2=re.compile(r"Address[^:]*:\s*([\w\s,\\.\-\/\&]+?)(?=[\r\n]+\s*Invoice_date)")
                            match13=regex2.search(text)
                            match14=re.findall(r'Currency\s+{selectanyone}|Currency{select anyone}|Currency{selectanyone}|Currency\s+{selec anyone}:(\s+\w+|\w+)',text)
                            match15=re.findall(r'Your_address:(([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+)|([\w\s]+),([\w\s]+),([\w\s]+)|([\w\s]+),([\w\s]+)|([\w\s]+))',text)
                            match16=re.findall(r'Enter_city:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            match17=re.findall(r'Enter_country:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            match18=re.findall(r'Enter_postal:((\s+\w+)|\w+)',text)
                            pattern=re.compile(r"(\d+\. +) +(\d+)\t* +(\d+|[\d,.,\d]+)([\w\s]+)\n",re.DOTALL)
                            print(match1)
                            ad_1 = match2.group(1).replace("\n", " ").replace("  ", "").strip()
                            ad = match13.group(1).replace("\n", " ").replace("  ", "").strip()
                            cn=match1.group(1).replace("\n", " ").replace("  ", "").strip()
                            bt=match3.group(1).replace("\n", " ").replace("  ", "").strip()



                            invd=""
                            invd=invd.join(match5[0])
                            invd2=""
                            invd2=invd2.join(match5[1])

                            # new_var_2 = match1[0][0].strip()
                            # cn=""
                            # cn=cn.join(new_var_2)

                            # new_var_3 = match3[0][0].strip()
                            # bt=""
                            # bt=bt.join(new_var_3)

                            new_var_4 = match4[0][0].strip()
                            invn=""
                            invn=invn.join(new_var_4)

                            # new_var_5 = match13[0][0].strip()
                            # ad=""
                            # ad=ad.join(new_var_5)

                            new_var_6 = match6[0][0].strip()
                            ci=""
                            ci=ci.join(new_var_6)

                            new_var_7 = match7[0][0].strip()
                            ct=""
                            ct=ct.join(new_var_7)

                            new_var_8 = match8[0][0].strip()
                            pt=""
                            pt=pt.join(new_var_8)

                            sa= ad+ ", "+ ci+ ", "+ ct+ ", "+pt
                            st15= 'null'

                            matches = re.findall(pattern, text)

                            items=[]

                            if matches==[]:
                                print("Sr. No.:",st15)
                                print("Quantity:",st15)
                                print("Unit price",st15)
                                print("Product:null",st15)
                            else:
                             i=0
                             for Srno,Quantity,Price, qwerty in matches:
                                    qwerty= " ".join(matches[i][3].split())
                                    # print(qwerty)
                                    Srno= " ".join(matches[i][0].split())

                                    print("Sr. No.:", Srno)
                                    Quantity = Quantity.replace(",", "")
                                    Quantity_1=int(Quantity)
                                    print("Quantity:", Quantity_1)
                                    Price = Price.replace(",", "")
                                    Price_1=float(Price)
                                    print("Unit price:", Price_1)
                                    print("Product:",qwerty) 
                                    items.append({
                                        "sr_no":Srno, "qty": Quantity_1, "unt_pr": Price_1, "product": qwerty
                                    })
                                    i+=1

                            # new_var_15 = match15[0][0].strip()
                            # ad_1=""
                            # ad_1=ad_1.join(new_var_15)
                            # field = [re.sub('\s+', ' ', s.strip().replace('\n', '')) for s in match15[0] if s.strip()]
                            # ad_1= "".join(field[0][:4]) + "" + "".join(field[0][4:])

                            new_var_16 = match16[0][0].strip()
                            ci_1=""
                            ci_1=ci_1.join(new_var_16)

                            new_var_17 = match17[0][0].strip()
                            ct_1=""
                            ct_1=ct_1.join(new_var_17)

                            new_var_18 = match18[0][0].strip()
                            pt_1=""
                            pt_1=pt_1.join(new_var_18)

                            ca= ad_1+ ", "+ ci_1+ ", "+ ct_1+ ", "+pt_1
                           
                            print("Company_name:",cn)
                            a= 'Invoice'
                            if a in match1[0][1]:
                                print("Invoice Number:",st15)
                                #final_data["invoice_numner"] = None
                            else:
                                print("Invoice Number:",invn)

                            print("Invoice date:",invd)
                            print("Invoice_due_date:",invd2)
                            print("Bill To:",bt)
                            print("Company address:",ca)
                            print("Shipping address:",sa)

                            subt= " ".join(match9[0][0].split())
                            subt = subt.replace(",", "")
                            subt_1=float(subt)
                            print("Subtotal:",subt_1)

                            shp= " ".join(match10[0][0].split())
                            shp = shp.replace(",", "")
                            shp_1=float(shp)
                            print("Shipping:",shp_1)

                            tx= " ".join(match11[0][0].split())
                            tx = tx.replace(",", "")
                            tx_1=float(tx)
                            print("Tax:",tx_1)

                            ttl= " ".join(match12[0][0].split())
                            ttl = ttl.replace(",", "")
                            ttl_1=float(ttl)
                            print("Total:",ttl_1)

                            cu= " ".join(match14[0].split())
                            print("Currency:",cu)

                            from datetime import datetime
                            import pytz

                            date_str = invd
                            invoice_date = datetime.strptime(date_str, '%d/%m/%y')
                            date_obj_utc = pytz.utc.localize(invoice_date)
                            date_obj= date_obj_utc.isoformat()
                            invd_1 = datetime.fromisoformat(date_obj)

                            date_str_2 = invd2
                            invoice_date_2 = datetime.strptime(date_str_2, '%d/%m/%y')
                            date_obj_utc_2 = pytz.utc.localize(invoice_date_2)
                            date_obj_2= date_obj_utc_2.isoformat()
                            invd_2 = datetime.fromisoformat(date_obj_2)

                            # create a MongoDB client
                            # client = MongoClient('mongodb+srv://Satya:satya@cluster0.pw10azv.mongodb.net/?retryWrites=true&w=majority')
                            client = MongoClient('mongodb://localhost:27017')

                            # specify the database and collection
                            db = client['mydatabase']
                            collection = db['invoices']
                            # define the invoice document to be inserted
                            document = {
                                'invoice_date': invd_1,
                                'invoice_due_date': invd_2,
                                'invoice_number': st15 if match1[0][1] == a else invn,
                                'order_from': cn,
                                'company_address': ca,
                                'contact_no':st15,
                                'Bill_to': bt,
                                'name':st15,
                                'shipping_address': sa,
                                'phone':st15,
                                'email':st15,
                                'items': st15 if matches == [] else items,
                                'Currency':cu,
                                'Subtotal':subt_1,
                                'Shipping':shp_1,
                                'Tax':tx_1,
                                'Total':ttl_1,
                                "ABN":st15,
                                "Rego": st15,
                                "Make": st15,
                                "Model": st15,
                                "Odometer":st15,
                                'user_id':ObjectId(user_id)


                            }

                            old_data_1 = collection.find_one({"invoice_number": document['invoice_number']})
                            print("OldData ===================================", old_data_1)
                            # insert the invoice document into the collection
                            if old_data_1 :
                                print("Already Added")
                            else :
                                result = collection.insert_one(document)
                                print('Inserted document ID:', result.inserted_id)

                        ###########
                        elif "Name" in text:
                            import re
                            match=re.findall(r'\d+[/.-]\d+[/.-]\d+', text)
                            match1=re.findall(r'Invoice number:(\s+(\w+)|(\w+))', text)
                            
                            # match2=re.findall(r'Company:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            regex12=re.compile(r"Company[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Name)")
                            match2=regex12.search(text)
                            match3=re.findall(r'Name:(\s+(\w+(?: \w+){1,10})|(\w+(?: \w+){1,10})|\w+|\s+\w+)',text)
                            match4=re.findall(r'(\s+[a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+[a-zA-Z]|([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+[a-zA-Z]))',text)
                            match45=re.findall(r'Phone:((\+\d+\s+\d+)|(\+\d+)|(\s+\+\d+\s+\d+)|(\s+\+\d+)|(\d+)|(\s+\d+))',text)
                            match46=re.findall(r'Contact_No:((\+\d+\s+\d+)|(\+\d+)|(\s+\+\d+\s+\d+)|(\s+\+\d+)|(\d+)|(\s+\d+))',text)
                            match5=re.findall(r'Subtotal:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match6=re.findall(r'Shipping:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match7=re.findall(r'Tax:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match8=re.findall(r'Total:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            # match9=re.findall(r'(\d+)\s+([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\-\d+\s+\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\-\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\\\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)',text)
                            regex=re.compile(r"Shipping\s+Address[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Phone)")
                            match9 = regex.search(text)
                            regex2= re.compile(r"Company\s+address[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Contact)")
                            match10 =regex2.search(text)
                            # match9=regex.search(text)
                            # match13=re.findall(r'Order_From:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            regex13=re.compile(r"Order_From[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Company\s+address)")
                            match13=regex13.search(text)
                            match14=re.findall(r'Currency\s+{selectanyone}|Currency{select anyone}|Currency{selectanyone}|Currency\s+{selec anyone}:(\s+\w+|\w+)',text)
                            # pattern=re.compile(r"(\d+\. +) +(\d+)\t* +(\d+|[\d,]+)([\w\s]+)\n",re.DOTALL)
                            pattern=re.compile(r"(\d+\. +) +(\d+)\t* +(\d+|[\d,.,\d]+)([\w\s]+)\n",re.DOTALL)


                           
                            sa = match9.group(1).strip()
                            ca=match10.group(1).strip()
                            cn=match2.group(1).strip()
                            of=match13.group(1).strip()

                            
                            invd=" "
                            invd=invd.join(match)

                            
                            # print(type(match))
                            #print(match1)
                            # st1=""
                            # st1=st1.join(match1
                            new_var_1 = match1[0][0].strip()
                            invn=""
                            invn=invn.join(new_var_1)
                            # a= '\n                                                   Invoice'
                            # if a in match1[0][0]:
                            #     print("Invoice number: null")
                            # else:
                            #     print("Invoice Number",st1
                            # new_var_2 = match2[0][0].strip()
                            # cn=""
                            # cn=cn.join(new_var_2)
                            new_var_3=match3[0][0].strip()
                            n=""
                            n=n.join(new_var_3)
                            new_var_4= match4[0][0].strip()
                            em=""
                            em=em.join(new_var_4)
                            new_var_45= match45[0][0].strip()
                            ph=""
                            ph=ph.join(new_var_45)
                            new_var_46= match46[0][0].strip()
                            con=""
                            con=con.join(new_var_46)
                            new_var_13= match13[0][0].strip()
                            # of=""
                            # of=of.join(new_var_13)
                            # new_var_9 = match9[1][0:]
                            # st9=""
                            # st9=st9.join(new_var_9
                            # new_var_3 = match9[3][0:]
                            # st10=""
                            # st10=st10.join(new_var_3)
                            new_var_5=match5[0][0]
                            subt=""
                            subt=subt.join(new_var_5)
                            new_var_6=match6[0][0]
                            shp=""
                            shp=shp.join(new_var_6)
                            new_var_7=match7[0][0]
                            tx=""
                            tx=tx.join(new_var_7)
                            new_var_8=match8[0][0]
                            ttl=""
                            ttl=ttl.join(new_var_8)
                            cu=" "
                            cu=cu.join(match14)
                            st15= 'null'
                            st16='null'
                            # st6=" "
                            # st6=st6.join(match6
                            # st7=" "
                            # st7=st7.join(match7)
                            #st5 = list(map(float,match5)) 
                            # st6 = list(map(float,match6)) 
                            # st7 = list(map(float,match7)) 
                            #st8 = list(map(float,match8))
                            #final_data= {}
                            from datetime import datetime
                            import pytz

                            date_str = invd
                            invoice_date = datetime.strptime(date_str, '%d/%m/%y')
                            date_obj_utc = pytz.utc.localize(invoice_date)
                            date_obj= date_obj_utc.isoformat()
                            invd_1 = datetime.fromisoformat(date_obj)

                            print("Invoice Date:", invd_1)
  

                            a= 'Invoice'
                            if a in match1[0][1]:
                                print("Invoice Number:",st15)
                                #final_data["invoice_numner"] = None
                            else:
                                print("Invoice Number:",invn)
                                #final_data["invoice_numner"] = st
                            print("Company Name:", cn)
                            print("Name:", n)
                            
                            # fields = [re.sub('\s+', ' ', s.strip().replace('\n', '')) for s in match9[1] if s.strip()]
                            # sa = ", ".join(fields[:4]) + ", " + " ".join(fields[4:])
                            # print("Shipping Address:", sa)
                            # #print("SA:", T)
                            print("Phone:",ph)
                            if match4==[]:
                                print("Email Address:", st16)
                            else:
                                print("Email Address:",em)
                                print("Order from:",of)
                            # field = [re.sub('\s+', ' ', s.strip().replace('\n', '')) for s in match9[3] if s.strip()]
                            # ca= ", ".join(field[:4]) + ", " + " ".join(field[4:])
                            # print("Company Address:", ca)
                            # #print("CA:", st10)
                            print("Contact no:",con)
                            print("#######Table content##########")
                            matches = re.findall(pattern, text)
                            items=[]
                            if matches==[]:
                                print("Sr. No.:",st15)
                                print("Quantity:",st15)
                                print("Unit price",st15)
                                print("Product:null",st15)
                            else:
                                i=0
                                for Srno,Quantity,Price, qwerty in matches:
                                        qwerty= " ".join(matches[i][3].split())
                                        Srno= " ".join(matches[i][0].split())
                                        print("Sr. No.:", Srno)
                                        Quantity = Quantity.replace(",", "")
                                        Quantity_1=int(Quantity)
                                        print("Quantity:", Quantity_1)
                                        Price = Price.replace(",", "")
                                        Price_1=float(Price)
                                        print("Unit price:", Price_1)
                                        print("Product:",qwerty) 
                                        items.append({
                                            "sr_no":Srno, "qty": Quantity_1, "unt_pr": Price_1, "product": qwerty
                                        })
                                        i+=1
                            print("#############")
                            cu= " ".join(match14[0].split())
                            print("Currency:",cu)
                            subt= " ".join(match5[0][0].split())
                            subt = subt.replace(",", "")
                            subt_1=float(subt)
                            print("Subtotal:",subt_1)
                            shp= " ".join(match6[0][0].split())
                            shp = shp.replace(",", "")
                            shp_1=float(shp)
                            print("Shipping:",shp_1)
                            tx= " ".join(match7[0][0].split())
                            tx = tx.replace(",", "")
                            tx_1=float(tx)
                            print("Tax:",tx_1)
                            ttl= " ".join(match8[0][0].split())
                            ttl = ttl.replace(",", "")
                            ttl_1=float(ttl)
                            print("Total:",ttl_1)

                            ######Storing in database#########
                            
                            client = MongoClient('mongodb://localhost:27017')
                            # specify the database and collection
                            db = client['mydatabase']
                            collection = db['invoices']
                            

                            # define the invoice document to be inserted
                            document = {
                                'invoice_date': invd_1,
                                'invoice_due_date': st16,
                                'invoice_number': st15 if match1[0][1] == a else invn,
                                'order_from': of,
                                'company_address': ca,
                                'contact_no': con,
                                'Bill_to': cn,
                                'name': n,
                                'shipping_address': sa,
                                'phone': ph,
                                'email': st16 if match4 == [] else em ,
                                'items': st15 if matches == [] else items,
                                'Currency':cu,
                                'Subtotal':subt_1,
                                'Shipping':shp_1,
                                'Tax':tx_1,
                                'Total':ttl_1,
                                "ABN":st15,
                                "Rego": st15,
                                "Make": st15,
                                "Model": st15,
                                "Odometer":st15,
                                'user_id': ObjectId(user_id)



                                

                                 
                            }
                            

                            old_data = collection.find_one({"invoice_number": document['invoice_number']})
                            print("OldData ===================================", old_data)
                            # insert the invoice document into the collection
                            if old_data :
                                print("Already Added")
                            else :
                                result = collection.insert_one(document)
                                print('Inserted document ID:', result.inserted_id)

                        # print the ID of the inserted document

                        elif "Rego" in text :
                            import re
                            match=re.findall(r'\d+[/.-]\d+[/.-]\d+', text)
                            match1=re.findall(r'Invoice_number:(\s+(\w+)|(\w+))', text)
                            regex200=re.compile(r'Ship_to[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Shipping)')
                            match2=regex200.search(text)
                            # match2=re.findall(r'Ship_to:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            # match3=re.findall(r'Name:(\s+(\w+(?: \w+){1,10})|(\w+(?: \w+){1,10})|\w+|\s+\w+)',text)
                            match4=re.findall(r'(\s+[a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+[a-zA-Z]|([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+[a-zA-Z]))',text)
                            match45=re.findall(r'Phone:((\+\d+\s+\d+)|(\+\d+)|(\s+\+\d+\s+\d+)|(\s+\+\d+)|(\d+)|(\s+\d+))',text)
                            match46=re.findall(r'Contact_No:((\+\d+\s+\d+)|(\+\d+)|(\s+\+\d+\s+\d+)|(\s+\+\d+)|(\d+)|(\s+\d+))',text)
                            match5=re.findall(r'Subtotal:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match6=re.findall(r'Shipping:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match7=re.findall(r'Tax:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match8=re.findall(r'Total:(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            # match9=re.findall(r'(\d+)\s+([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\-\d+\s+\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\-\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\\\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)',text)
                            regex=re.compile(r"Shipping\s+Address[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Contact)")
                            match9 = regex.search(text)
                            regex2= re.compile(r"Company\s+address[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Email)")
                            match10 =regex2.search(text)
                            # match13=re.findall(r'Company_name:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            regex13=re.compile(r"Company_name[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Company)")
                            match13=regex13.search(text)
                            match14=re.findall(r'Currency\s+{selectanyone}|Currency{select anyone}|Currency{selectanyone}|Currency\s+{selec anyone}:(\s+\w+|\w+)',text)
                            match15=re.findall(r'ABN:(\s+(\w+)|(\w+))', text)
                            match16=re.findall(r'Rego:(\s+(\w+)|(\w+))', text)
                            match17=re.findall(r'Make:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            match18=re.findall(r'Model:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            match19=re.findall(r'Odometer:(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*)))',text)
                            pattern=re.compile(r"(\d+\. +) +(\d+)\t* +(\d+|[\d,.,\d]+)([\w\s]+)\n",re.DOTALL)

                            print(match)
                            sa = match9.group(1).strip()
                            ca=match10.group(1).strip()
                            of=match13.group(1).strip()
                            cn=match2.group(1).strip()
                            print(ca)

                            print(pattern)
                            invd=" "
                            invd=invd.join(match)

                            invd2=" "
                            invd2=invd2.join(match)
                            print(invd)
                            print(invd2)

                            
                            # print(type(match))
                            #print(match1)
                            # st1=""
                            # st1=st1.join(match1
                            new_var_1 = match1[0][0].strip()
                            invn=""
                            invn=invn.join(new_var_1)


                            new_var_15 = match15[0][0].strip()
                            abn=""
                            abn=abn.join(new_var_15)

                            new_var_16 = match16[0][0].strip()
                            rego=""
                            rego=rego.join(new_var_16)

                            # a= '\n                                                   Invoice'
                            # if a in match1[0][0]:
                            #     print("Invoice number: null")
                            # else:
                            #     print("Invoice Number",st1
                            # new_var_2 = match2[0][0].strip()
                            # cn=""
                            # cn=cn.join(new_var_2)
                            new_var_17=match17[0][0].strip()
                            mk=""
                            mk=mk.join(new_var_17)
                            new_var_18=match18[0][0].strip()
                            mod=""
                            mod=mod.join(new_var_18)


                            new_var_4= match4[0][0].strip()
                            em=""
                            em=em.join(new_var_4)
                            new_var_45= match45[0][0].strip()
                            ph=""
                            ph=ph.join(new_var_45)
                            new_var_46= match46[0][0].strip()
                            con=""
                            con=con.join(new_var_46)
                            # new_var_13= match13[0][0].strip()
                            # of=""
                            # of=of.join(new_var_13)
                            # new_var_9 = match9[1][0:]
                            # st9=""
                            # st9=st9.join(new_var_9
                            # new_var_3 = match9[0][0:]
                            # st10=""
                            # st10=st10.join(new_var_3)
                            new_var_5=match5[0][0]
                            subt=""
                            subt=subt.join(new_var_5)
                            new_var_6=match6[0][0]
                            shp=""
                            shp=shp.join(new_var_6)
                            new_var_7=match7[0][0]
                            tx=""
                            tx=tx.join(new_var_7)
                            new_var_8=match8[0][0]
                            ttl=""
                            ttl=ttl.join(new_var_8)
                            new_var_19=match19[0][0]
                            od=""
                            od=od.join(new_var_19)


                            cu=" "
                            cu=cu.join(match14)
                            st15= 'null'
                            st16='null'
                            # st6=" "
                            # st6=st6.join(match6
                            # st7=" "
                            # st7=st7.join(match7)
                            #st5 = list(map(float,match5)) 
                            # st6 = list(map(float,match6)) 
                            # st7 = list(map(float,match7)) 
                            #st8 = list(map(float,match8))
                            #final_data= {}
                            from datetime import datetime
                            import pytz

                            date_str = invd
                            invoice_date = datetime.strptime(date_str, '%d/%m/%y')
                            date_obj_utc = pytz.utc.localize(invoice_date)
                            date_obj= date_obj_utc.isoformat()
                            invd_1 = datetime.fromisoformat(date_obj)

                            print("Invoice Date:", invd_1)
  
                            date_str_2 = invd2
                            invoice_date_2 = datetime.strptime(date_str_2, '%d/%m/%y')
                            date_obj_utc_2 = pytz.utc.localize(invoice_date_2)
                            date_obj_2= date_obj_utc_2.isoformat()
                            invd_2 = datetime.fromisoformat(date_obj_2)
                            print("Invoice Due Date:", invd_2)  

                            # invd_1 = invoice_date.isoformat(
                            print("Invoice Date:", invd_1)  
                            a= 'Invoice'
                            if a in match1[0][1]:
                                print("Invoice Number:",st15)
                                #final_data["invoice_numner"] = None
                            else:
                                print("Invoice Number:",invn)
                                #final_data["invoice_numner"] = st
                            print("Company Name:", cn)
                            
                            # fields = [re.sub('\s+', ' ', s.strip().replace('\n', '')) for s in match9[2] if s.strip()]
                            # sa = ", ".join(fields[:4]) + ", " + " ".join(fields[4:])
                            # print("Shipping Address:", sa)
                            #print("SA:", T)
                            print("Phone:",ph)
                            if match4==[]:
                                print("Email Address:", st16)
                            else:
                                print("Email Address:",em)
                                print("Order from:",of)
                            # field = [re.sub('\s+', ' ', s.strip().replace('\n', '')) for s in match9[0] if s.strip()]
                            # ca= ", ".join(field[:4]) + ", " + " ".join(field[4:])
                            # print("Company Address:", ca)
                            #print("CA:", st10)
                            print("Contact no:",con)
                            print("#######Table content##########")
                            matches = re.findall(pattern, text)
                            items=[]
                            if matches==[]:
                                print("Sr. No.:",st15)
                                print("Quantity:",st15)
                                print("Unit price",st15)
                                print("Product:null",st15)
                            else:
                                i=0
                                for Srno,Quantity,Price, qwerty in matches:
                                        qwerty= " ".join(matches[i][3].split())
                                        # print(qwerty)
                                        Srno= " ".join(matches[i][0].split())
                                        print("Sr. No.:", Srno)
                                        Quantity = Quantity.replace(",", "")
                                        Quantity_1=int(Quantity)
                                        print("Quantity:", Quantity_1)
                                        Price = Price.replace(",", "")
                                        Price_1=float(Price)
                                        print("Unit price:", Price_1)
                                        print("Product:",qwerty) 
                                        items.append({
                                            "sr_no":Srno, "qty": Quantity_1, "unt_pr": Price_1, "product": qwerty
                                        })
                                        i+=1
                            print("#############")
                            cu= " ".join(match14[0].split())
                            print("Currency:",cu)
                            subt= " ".join(match5[0][0].split())
                            subt = subt.replace(",", "")
                            subt_1=float(subt)
                            print("Subtotal:",subt_1)
                            shp= " ".join(match6[0][0].split())
                            shp = shp.replace(",", "")
                            shp_1=float(shp)
                            print("Shipping:",shp_1)
                            tx= " ".join(match7[0][0].split())
                            tx = tx.replace(",", "")
                            tx_1=float(tx)
                            print("Tax:",tx_1)
                            ttl= " ".join(match8[0][0].split())
                            ttl = ttl.replace(",", "")
                            ttl_1=float(ttl)
                            print("Total:",ttl_1)
                            od= " ".join(match19[0][0].split())
                            od = od.replace(",", "")
                            od_1=float(od)
                            print("Odometer:",od_1)

                            ######Storing in database#########
                            
                            client = MongoClient('mongodb://localhost:27017')
                            # specify the database and collection
                            db = client['mydatabase']
                            collection = db['invoices']
                            #invoices_collection = db['invoices']
                            #users_collection = db['users']


                            # define the invoice document to be inserted
                            document = {
                                'invoice_date': invd_1,
                                'invoice_due_date': invd_2,
                                'invoice_number': st15 if match1[0][1] == a else invn,
                                'order_from': of,
                                'company_address': ca,
                                'contact_no': con,
                                'Bill_to': cn,
                                'name': st15,
                                'shipping_address': sa,
                                'phone': ph,
                                'email': st16 if match4 == [] else em ,
                                'items': st15 if matches == [] else items,
                                'Currency':cu,
                                'Subtotal':subt_1,
                                'Shipping':shp_1,
                                'Tax':tx_1,
                                'Total':ttl_1,
                                "ABN":abn,
                                "Rego": rego,
                                "Make": mk,
                                "Model": mod,
                                "Odometer":od_1,
                                'user_id': ObjectId(user_id)

                                
                                
                                 
                            }
                            #invoices_collection.insert_one(document)
                            

                            old_data = collection.find_one({"invoice_number": document['invoice_number']})
                            print("OldData ===================================", old_data)
                            # insert the invoice document into the collection
                            if old_data :
                                print("Already Added")
                            else :
                                result = collection.insert_one(document)
                                print('Inserted document ID:', result.inserted_id)


                        elif "Freight" in text :
                            import re
                            match=re.findall(r'\d+[/.-]\d+[/.-]\d+', text)
                            match1=re.findall(r' Purchase Order# :(\s+(\w+)|(\w+))', text)
                            regex100=re.compile(r"Ship_to[^:]*:\s*([\w\s,\\.\-\/\&]+?)(?=[\r\n]+\s*Shipping)")
                            match2=regex100.search(text)
                            # match3=re.findall(r'Name:(\s+(\w+(?: \w+){1,10})|(\w+(?: \w+){1,10})|\w+|\s+\w+)',text)
                            match4=re.findall(r'(\s+[a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+[a-zA-Z]|([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+[a-zA-Z]))',text)
                            # match45=re.findall(r'Phone:((\+\d+\s+\d+)|(\+\d+)|(\s+\+\d+\s+\d+)|(\s+\+\d+)|(\d+)|(\s+\d+))',text)
                            match46=re.findall(r'Contact_No:((\+\d+\s+\d+)|(\+\d+)|(\s+\+\d+\s+\d+)|(\s+\+\d+)|(\d+)|(\s+\d+))',text)
                            match5=re.findall(r'Subtotal(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match6=re.findall(r'Freight(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match7=re.findall(r'Tax(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            match8=re.findall(r'Total(\s+\d{1,10}(,\d{1,6})(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})(,\d{1,6})|\s+\d{1,10}(,\d{1,6})|(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*))))',text)
                            # match9=re.findall(r'(\d+)\s+([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\-\d+\s+\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\-\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)|(\w+\\\d+),([\w\s]+),([\w\s]+),([\w\s]+),([\w\s]+),([\d\s]+)',text)
                            regex=re.compile(r"Shipping_address[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Contact)")
                            match9 = regex.search(text)
                            regex2= re.compile(r"Address[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Email)")
                            match10 =regex2.search(text)
                            regex3= re.compile(r"Phone[^:]*:\s*([\w\s,\\.\-\/\+\(\)]+?)(?=[\r\n]+\s*ABN)")
                            match45=regex3.search(text)

                            # match13=re.findall(r'Company_name:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            regex13=re.compile(r"Company_name[^:]*:\s*([\w\s,\\.\-\/]+?)(?=[\r\n]+\s*Address)")
                            match13=regex13.search(text)
                            match14=re.findall(r'Currency\s+{selectanyone}|Currency{select anyone}|Currency{selectanyone}|Currency\s+{select anyone}:(\s+\w+|\w+)',text)
                            match15=re.findall(r'ABN:(\s+(\w+)|(\w+))', text)
                            # match16=re.findall(r'Rego:(\s+(\w+)|(\w+))', text)
                            # match17=re.findall(r'Make:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            # match18=re.findall(r'Model:(\s+(\w+(?: \w+){1,10})|\s+(\w+(?:\w+){1,10})|(\w+(?: \w+){1,10})|(\w+(?:\w+){1,10}))',text)
                            # match19=re.findall(r'Odometer:(\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|(\s+[\$\£\€\₹](\d+(?:\.\d{1,2})?)|\s+(\d+(?:\.\d{1,2})?)|(\s+\w+(\d+(?:\.\d{1,2})?))|(\s+\w+\s+(\d+(?:\.\d{1,2})?))|\s+[\$\£\€\₹]\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+[\$\£\€\₹]\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|[\$\£\€\₹]\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+(\d+(?:\.\d{1,2})?)(\d{1,10}(,\d{1,6})*(\.\d{1,4})?|\s+\d{1,10}(,\d{1,6})*(\.\d{1,4})?)|\s+(\d{1,3}(,\d{3})*)))',text)
                            pattern=re.compile(r"(\d+\. +) +(\d+)\t* +(\d+|[\d,.,\d]+)([\w\s]+)\n",re.DOTALL)

                           
                            sa = match9.group(1).strip()
                            ca=match10.group(1).strip()
                            cn=match2.group(1).strip()
                            of=match13.group(1).strip()
                            ph=match45.group(1).strip()
                            invd=""
                            invd=invd.join(match[0])
                            print(invd)

                            invd2=""
                            invd2=invd2.join(match[1])
                            print(invd2)
                            
                            # print(type(match))
                            #print(match1)
                            # st1=""
                            # st1=st1.join(match1
                            new_var_1 = match1[0][0].strip()
                            invn=""
                            invn=invn.join(new_var_1)


                            new_var_15 = match15[0][0].strip()
                            abn=""
                            abn=abn.join(new_var_15)

                            # new_var_16 = match16[0][0].strip()
                            # rego=""
                            # rego=rego.join(new_var_16)

                            # a= '\n                                                   Invoice'
                            # if a in match1[0][0]:
                            #     print("Invoice number: null")
                            # else:
                            #     print("Invoice Number",st1
                            # new_var_2 = match2[0][0].strip()
                            # cn=""
                            # cn=cn.join(new_var_2)
                            # new_var_17=match17[0][0].strip()
                            # mk=""
                            # mk=mk.join(new_var_17)
                            # new_var_18=match18[0][0].strip()
                            # mod=""
                            # mod=mod.join(new_var_18)


                            new_var_4= match4[0][0].strip()
                            em=""
                            em=em.join(new_var_4)
                            # new_var_45= match45[0][0].strip()
                            # ph=""
                            # ph=ph.join(new_var_45)
                            new_var_46= match46[0][0].strip()
                            con=""
                            con=con.join(new_var_46)
                            # new_var_13= match13[0][0].strip()
                            # of=""
                            # of=of.join(new_var_13)
                            # new_var_9 = match9[1][0:]
                            # st9=""
                            # st9=st9.join(new_var_9
                            # new_var_3 = match9[0][0:]
                            # st10=""
                            # st10=st10.join(new_var_3)
                            new_var_5=match5[0][0]
                            subt=""
                            subt=subt.join(new_var_5)
                            new_var_6=match6[0][0]
                            shp=""
                            shp=shp.join(new_var_6)
                            new_var_7=match7[0][0]
                            tx=""
                            tx=tx.join(new_var_7)
                            new_var_8=match8[0][0]
                            ttl=""
                            ttl=ttl.join(new_var_8)
                            # new_var_19=match19[0][0]
                            # od=""
                            # od=od.join(new_var_19)


                            cu=" "
                            cu=cu.join(match14)
                            st15= 'null'
                            st16='null'
                            # st6=" "
                            # st6=st6.join(match6
                            # st7=" "
                            # st7=st7.join(match7)
                            #st5 = list(map(float,match5)) 
                            # st6 = list(map(float,match6)) 
                            # st7 = list(map(float,match7)) 
                            #st8 = list(map(float,match8))
                            #final_data= {}
                            from datetime import datetime
                            import pytz

                            date_str = invd
                            invoice_date = datetime.strptime(date_str, '%d/%m/%y')
                            date_obj_utc = pytz.utc.localize(invoice_date)
                            date_obj= date_obj_utc.isoformat()
                            invd_1 = datetime.fromisoformat(date_obj)

                            date_str_2 = invd2
                            invoice_date_2 = datetime.strptime(date_str_2, '%d/%m/%y')
                            date_obj_utc_2 = pytz.utc.localize(invoice_date_2)
                            date_obj_2= date_obj_utc_2.isoformat()
                            invd_2 = datetime.fromisoformat(date_obj_2)
                            # print("Invoice Date:", invd_1)
                            # print("Invoice Due Date:", invd_2)  

                            # invd_1 = invoice_date.isoformat(
                            # print("Invoice Date:", invd_1)  
                            a= 'Invoice'
                            if a in match1[0][1]:
                                print("Invoice Number:",st15)
                                #final_data["invoice_numner"] = None
                            else:
                                print("Invoice Number:",invn)
                                #final_data["invoice_numner"] = st
                            print("Company Name:", cn)
                            
                            # fields = [re.sub('\s+', ' ', s.strip().replace('\n', '')) for s in match9[2] if s.strip()]
                            # sa = ", ".join(fields[:4]) + ", " + " ".join(fields[4:])
                            # print("Shipping Address:", sa)
                            #print("SA:", T)
                            print("Phone:",ph)
                            if match4==[]:
                                print("Email Address:", st16)
                            else:
                                print("Email Address:",em)
                                print("Order from:",of)
                            # field = [re.sub('\s+', ' ', s.strip().replace('\n', '')) for s in match9[0] if s.strip()]
                            # ca= ", ".join(field[:4]) + ", " + " ".join(field[4:])
                            # print("Company Address:", ca)
                            #print("CA:", st10)
                            print("Contact no:",con)
                            print("#######Table content##########")
                            matches = re.findall(pattern, text)
                            items=[]
                            if matches==[]:
                                print("Sr. No.:",st15)
                                print("Quantity:",st15)
                                print("Unit price",st15)
                                print("Product:null",st15)
                            else:
                                i=0
                                for Srno,Quantity,Price, qwerty in matches:
                                        qwerty= " ".join(matches[i][3].split())
                                        # print(qwerty)
                                        Srno= " ".join(matches[i][0].split())
                                        print("Sr. No.:", Srno)
                                        Quantity = Quantity.replace(",", "")
                                        Quantity_1=int(Quantity)
                                        print("Quantity:", Quantity_1)
                                        Price = Price.replace(",", "")
                                        Price_1=float(Price)
                                        print("Unit price:", Price_1)
                                        print("Product:",qwerty) 
                                        items.append({
                                            "sr_no":Srno, "qty": Quantity_1, "unt_pr": Price_1, "product": qwerty
                                        })
                                        i+=1
                            print("#############")
                            cu= " ".join(match14[0].split())
                            print("Currency:",cu)
                            subt= " ".join(match5[0][0].split())
                            subt = subt.replace(",", "")
                            # subt10=float(subt)
                            subt_1=float(subt)
                            print("Subtotal:",subt_1)
                            shp= " ".join(match6[0][0].split())
                            shp = shp.replace(",", "")
                            # shp10=float(shp)
                            shp_1=float(shp)
                            print("Freight:",shp_1)
                            tx= " ".join(match7[0][0].split())
                            tx = tx.replace(",", "")
                            # tx10=float(tx)
                            tx_1=float(tx)
                            print("Tax:",tx_1)
                            ttl= " ".join(match8[0][0].split())
                            ttl = ttl.replace(",", "")
                            # ttl10=float(ttl)
                            ttl_1=float(ttl)
                            print("Total:",ttl_1)
                            # od= " ".join(match19[0][0].split())
                            # od = od.replace(",", "")
                            # od_1=int(od)
                            # print("Odometer:",od_1)

                            ######Storing in database#########
                            
                            client = MongoClient('mongodb://localhost:27017')
                            # specify the database and collection
                            db = client['mydatabase']
                            collection = db['invoices']
                            #invoices_collection = db['invoices']
                            #users_collection = db['users']


                            # define the invoice document to be inserted
                            document = {
                                'invoice_date': invd_1,
                                'invoice_due_date': invd_2,
                                'invoice_number': st15 if match1[0][1] == a else invn,
                                'order_from': of,
                                'company_address': ca,
                                'contact_no': con,
                                'Bill_to': cn,
                                'name': st15,
                                'shipping_address': sa,
                                'phone': ph,
                                'email': st16 if match4 == [] else em ,
                                'items': st15 if matches == [] else items,
                                'Currency':cu,
                                'Subtotal':subt_1,
                                'Shipping':shp_1,
                                'Tax':tx_1,
                                'Total':ttl_1,
                                "ABN":abn,
                                "Rego": st15,
                                "Make": st15,
                                "Model": st15,
                                "Odometer":st15,
                                'user_id': ObjectId(user_id)

                                
                                
                                 
                            }
                            #invoices_collection.insert_one(document)
                            

                            old_data = collection.find_one({"invoice_number": document['invoice_number']})
                            print("OldData ===================================", old_data)
                            # insert the invoice document into the collection
                            if old_data :
                                print("Already Added")
                            else :
                                result = collection.insert_one(document)
                                print('Inserted document ID:', result.inserted_id)

                        # print the ID of the inserted document
                        else:
                           return redirect('/wrong/')



    return render_template("dashboard.html")



####Imp#######
@app.route('/data/')
@login_required
def data():
    # Query for fetching data
    return render_template('data.html')
#################

@app.route('/user/signout')
def user_signout():
    print("before ", session)
    session.clear()
    print("after ", session)
    return redirect('/user/login')

@app.route('/user/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    else:
        email = request.form['email']
        user = db.users.find_one({'email': email})
        if user:
            # generate a unique password reset token and save it to the user's document in the database
            token = str(uuid.uuid4())
            timestamp = datetime.now() # add timestamp
            db.users.update_one({'_id': user['_id']}, {
                                '$set': {'password_reset_token': token, 'password_reset_timestamp': timestamp}})
            # send an email to the user's email address with the token
            send_reset_email(email, token)
            return render_template('reset_password_sent.html')
        else:
            # if the email address is not found in the database, show an error message on the same page
            return render_template('forgot_password.html', message='Email address not found')

@app.route('/user/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = db.users.find_one({'password_reset_token': token})
    if not user:
        # if the token is not found in the database, show an error message on the reset_password_invalid.html page
        return render_template('reset_password_invalid.html')

    # check if the password_reset_timestamp key exists in the user dictionary
    if 'password_reset_timestamp' in user:
        # get the timestamp when the password reset link was generated
        timestamp = user['password_reset_timestamp']
        # check if the link has expired (2 minutes since the link was generated)
        if (datetime.now() - timestamp).total_seconds() > 120:
            # if the link has expired, show an error message on the reset_password_invalid.html page
            return render_template('reset_password_invalid.html')

    if request.method == 'GET':
        # show the reset_password.html page with a hidden input field containing the token
        return render_template('reset_password.html', token=token)
    else:
        # update the user's password in the database and clear the password_reset_token
        password = request.form['password']
        # update user's password in the database
        hashed_password = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)
        db.users.update_one({"_id": user["_id"]}, {"$set": {"password": hashed_password}})
        # clear the password_reset_token and password_reset_timestamp
        db.users.update_one({"_id": user["_id"]}, {"$unset": {"password_reset_token": 1, "password_reset_timestamp": 1}})
        # send the new password to the user via email
        # code to send email goes here
        return redirect('/user/login')

# helper function to send the password reset email
def send_reset_email(email, token):
    # use your own email address and password to log in to the SMTP server
    # make sure to enable "Less secure app access" on your Google account to allow the script to access your account
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('satyashah26102001@gmail.com', 'prwjitxdinnmvokd')

    message = f"""Subject: Password Reset Request

    To reset your password, please click on the following link: http://localhost:5001/user/reset_password/{token}
    """
    server.sendmail('satyashah26102001@gmail.com', email, message)
    server.quit()

from routes import *
if __name__ == '__main__':
    app.run(debug=True, port=5001)




