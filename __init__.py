from email.policy import default
from genericpath import exists
from flask import Flask, request, jsonify, session, redirect, url_for, request, render_template, make_response
from flask_sqlalchemy import SQLAlchemy
import re
import datetime

from sqlalchemy import ForeignKey

app = Flask(__name__)
app.secret_key = 'hewwo? hewwo!'

# MySQL database connection configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:hewwo@localhost/data'  # Define the database URI for MySQL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking modifications for performance reasons
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=60)
session.permanent = True

# Initialize the database
db = SQLAlchemy(app)

#db object classes
class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)

    def __init__(self, username, password, address, email):
        self.username = username
        self.password = password
        self.address = address
        self.email = email

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "address": self.address,
            "email": self.email
        }

class admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "email": self.email
        }

class inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    productName = db.Column(db.String(50), nullable=False, unique=True)
    userID = db.Column(db.Integer, ForeignKey(user.id), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    price = db.Column(db.Decimal(5,2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, productName, userID, description, price, quantity):
        self.productName = productName
        self.userID = userID
        self.price = price
        self.quantity = quantity
        self.description = description

    def serialize(self):
        return {
            "id": self.id,
            "productname": self.productName,
            "description": self.description,
            "userID": self.userID,
            "price": self.price,
            "quantity": self.quantity
        }

#table creation


# Create the database and table when the app starts
with app.app_context():  # Use the app context to perform actions within the Flask application
    db.create_all()  # Create all tables defined by the models

#frontend stuff
def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('main'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        loginInfo = request.form
        userData = user.query.first(user.username == loginInfo['username'])

        if(userData is not None):
            if(loginInfo['pword'] == userData['password']):
                session['username'] = loginInfo['username']
                session['userID'] = userData['id']
                return redirect(url_for('main')), 200
            else:
                return jsonify({'error': 'Incorrect password'}), 401
        else:
            return jsonify({'error': 'Username not found'}), 404
    else:
        return render_template('login.html')

@app.route('/adminlogin', methods=['POST'])
def adminlogin():
    if request.method == 'POST':
        loginInfo = request.form
        adminData = admin.query.first(admin.username == loginInfo['username'])

        if(adminData is not None):
            if(loginInfo['pword'] == adminData['password']):
                session['adminuser'] = loginInfo['username']
                return redirect(url_for('admin')), 200
            else:
                return jsonify({'error': 'Incorrect password'}), 401
        else:
            return jsonify({'error': 'Username not found'}), 404
    else:
        render_template('adminlogin.html')

@app.route('/register', methods=["POST"])
def register():
    if request.method == 'POST':
        accountInfo = request.form
    
        if(accountInfo is None):
            return jsonify({'error': 'Missing form'}), 400
        if(accountInfo['username'] is None):
            return jsonify({'error': 'Missing username'}), 400
        if(accountInfo['password'] is None):
            return jsonify({'error': 'Missing password'}), 400
        if(accountInfo['address'] is None):
            return jsonify({'error': 'Missing address'}), 400
        if(accountInfo['email'] is None):
            return jsonify({'error': 'Missing email'}), 400
        if not validate_email(accountInfo['email']):
            return jsonify({'error': 'Invalid email'}), 400

        newUser = user(accountInfo['username'], accountInfo['password'], accountInfo['address'], accountInfo['email']) # password should *NEVER* be stored in plaintext in a real production environment but im just trying to get it done :skull:
        db.session.add(newUser)
        db.session.commit()
        return jsonify(newUser.serialize()), 201
    else:
        return render_template('register.html')

@app.route('/main')
def main():
    if 'username' in session:
        return render_template('main.html')
    else:
        return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if 'adminuser' in session:
        return render_template('admin.html')
    else:
        return redirect(url_for('index')), 401

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('userID', None)
    session.pop('adminuser', None)
    return "You have been logged out!"

#crud stuff
def ValidatePrice(priceStr):
    try:
        price = float(priceStr)
        return True
    except:
        return False

@app.route('/create', methods=['POST'])
def create():
    productInfo = request.form
    if ValidatePrice(productInfo['price']) is False:
        return jsonify({'error': 'could not convert string to float'}), 400

    if productInfo['description'] is None:
        desc = ""
    else:
        desc = productInfo['description']

    newProduct = inventory(productInfo['productname'], session['userID'], desc, productInfo['price'], productInfo['quantity'])
    db.session.add(newProduct)
    db.session.commit()
    return jsonify(newProduct.serialize()), 201

@app.route('/admincreate', methods=['POST'])
def create():
    productInfo = request.form
    if ValidatePrice(productInfo['price']) is False:
        return jsonify({'error': 'could not convert string to float'}), 400

    if productInfo['description'] is None:
        desc = ""
    else:
        desc = productInfo['description']

    newProduct = inventory(productInfo['productname'], productInfo['userID'], desc, productInfo['price'], productInfo['quantity'])
    db.session.add(newProduct)
    db.session.commit()
    return jsonify(newProduct.serialize()), 201

@app.route('/read', methods=['GET'])
def read():
    productID = request.form['itemid']
    product = inventory.query.get(productID)
    if product is None:
        return jsonify({'error': 'no such product exists'}), 404
    if product['userID'] != session['userID']:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify(product)

@app.route('/adminread', methods=['GET'])
def adminread():
    productID = request.form['itemid']
    product = inventory.query.get(productID)
    if product is None:
        return jsonify({'error': 'no such product exists'}), 404
    return jsonify(product)

@app.route('/readall', methods=['GET'])
def readall():
    products = inventory.query.filter(inventory.userID == session['userID'])
    return jsonify([user.serialize() for product in products])

@app.route('/adminreadall', methods=['GET'])
def adminreadall():
    products = inventory.query.all()
    return jsonify([user.serialize() for product in products])

@app.route('/update', methods=['POST'])
def update():
    productInfo = request.form
    product = inventory.query.get(productInfo['id'])
    if product is None:
        return jsonify({'error': 'no product with this id'}), 404
    if product['userID'] != session['userID']:
        return jsonify({'error': 'unauthorized'}), 401
    if productInfo['price'] is not None:
        if ValidatePrice(productInfo['price']) is False:
            return jsonify({'error': 'could not convert string to float'}), 400
        product.price = productInfo['price']
    if productInfo['productname'] is not None:
        product.productName = productInfo['productname']
    if productInfo['quantity'] is not None:
        product.quantity = productInfo['quantity']
    if productInfo['description'] is not None:
        product.description = productInfo['description']
        
    db.session.commit()
    return jsonify(productInfo.serialize()), 201

@app.route('/adminupdate', methods=['POST'])
def adminupdate():
    productInfo = request.form
    product = inventory.query.get(productInfo['id'])
    if product is None:
        return jsonify({'error': 'no product with this id'}), 404
    if productInfo['price'] is not None:
        if ValidatePrice(productInfo['price']) is False:
            return jsonify({'error': 'could not convert string to float'}), 400
        product.price = productInfo['price']
    if productInfo['userID'] is not None:
        product.userID = productInfo['userid']
    if productInfo['productname'] is not None:
        product.productName = productInfo['productname']
    if productInfo['quantity'] is not None:
        product.quantity = productInfo['quantity']
    if productInfo['description'] is not None:
        product.description = productInfo['description']
        
    db.session.commit()
    return jsonify(productInfo.serialize()), 201

@app.route('/delete', methods=['POST'])
def delete():
    productID = request.form['itemid']
    product = inventory.query.get(productID)
    if product is None:
        return jsonify({'error': 'no such product exists'}), 404
    if product['userID'] != session['userID']:
        return jsonify({'error': 'unauthorized'}), 401

    db.session.delete(product)
    db.session.commit()
    return jsonify({'info': 'successfully deleted'}), 200

@app.route('/admindelete', methods=['POST'])
def admindelete():
    productID = request.form['itemid']
    product = inventory.query.get(productID)
    if product is None:
        return jsonify({'error': 'no such product exists'}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({'info': 'successfully deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True)