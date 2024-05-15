from flask import request, session, jsonify
from passlib.hash import pbkdf2_sha256
from app import db
import uuid
import bcrypt
import datetime
import jwt

from datetime import timedelta

class User:
  
  def start_session(self, user):
    """
    This method is used to start a new session for the logged-in user.
    """
    del user['password']
    session['logged_in'] = True
    session['user'] = user
    user['_id'] = str(user['_id'])  # Convert ObjectId to string
    return jsonify({
        "user": user,
        "message": "Login successful"
    }), 200

  def signup(self):
    """
    This method is used to create a new user account.
    """
    # Get user input from the request object
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    # Hash the password
    hashed_password = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)

    # Create the user object
    user = {
      "name": name,
      "email": email,
      "password": hashed_password
    }

    # Check for existing email address
    if db.users.find_one({ "email": email }):
      return jsonify({ "error": "Email address already in use" }), 400

    # Insert new user into the database
    if db.users.insert_one(user):
      return self.start_session(user)

    return jsonify({ "error": "Signup failed" }), 400
  
  
  def signout(self):
    """
    This method is used to sign out the current user.
    """
    session.clear()
    return jsonify({
      "message": "You have been successfully signed out"
    }), 200
  
  
  # def login(self):
  #   """
  #   This method is used to log in a user.
  #   """
  #   # Get user input from the request object
  #   email = request.form.get('email')
  #   password = request.form.get('password')

  #   # Find user with matching email in the database
  #   user = db.users.find_one({ "email": email })

  #   # Check if the user exists and the password is correct
  #   if user and pbkdf2_sha256.verify(password, user['password']):
  #     return self.start_session(user)
    
  #   # Return error message if login fails
  #   return jsonify({ "error": "Invalid login credentials" }), 401
  

  def login(self):
    """
    This method is used to log in a user and generate a JWT token.
    """
    # Get user input from the request object
    email = request.form.get('email')
    password = request.form.get('password')

    # Find user with matching email in the database
    user = db.users.find_one({ "email": email })

    # Check if the user exists and the password is correct
    if user and pbkdf2_sha256.verify(password, user['password']):
      # Generate a JWT token
      payload = {
          'user_id': str(user['_id']),
          'exp': datetime.utcnow() + timedelta(days=1)
      }
      token = jwt.encode(payload, 'secret_key', algorithm='HS256')

      # Return the token as a JSON response
      return jsonify({ 'token': token })

    # Return error message if login fails
    return jsonify({ "error": "Invalid login credentials" }), 401



  def forgot_password(self):
      """
      This method is used to initiate the password reset process.
      """
      # Get user input from the request object
      email = request.form.get('email')

      # Find user with matching email in the database
      user = db.users.find_one({ "email": email })

      # Check if the user exists
      if not user:
          return jsonify({ "error": "Invalid email address" }), 400

      # Generate a new password reset token
      token = uuid.uuid4().hex

      # Update the user's record in the database with the new token
      db.users.update_one(
          { "email": email },
          { "$set": { "reset_token": token } }
      )

      # Send the password reset email to the user's email address
      # (Code to send the email goes here)

      return jsonify({
          "message": "Password reset email sent"
      }),200
