from email.policy import default
from genericpath import exists
from flask import *
from flask_sqlalchemy import SQLAlchemy
import re
import datetime
from decimal import *
from sqlalchemy import ForeignKey

app = Flask(__name__)
app.secret_key = 'hewwo? hewwo!'

# MySQL database connection configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:toor@localhost:3360/project1'  # Define the database URI for MySQL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking modifications for perjsonance reasons
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=60)

# Initialize the database
db = SQLAlchemy(app)

#db object classes
class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    pword = db.Column(db.String(250), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)

    def __init__(self, username, pword, address, email):
        self.username = username
        self.pword = pword
        self.address = address
        self.email = email

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.pword,
            "address": self.address,
            "email": self.email
        }

class admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    pword = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)

    def __init__(self, username, pword, email):
        self.username = username
        self.pword = pword
        self.email = email

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.pword,
            "email": self.email
        }

class inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    productName = db.Column(db.String(50), nullable=False, unique=True)
    userID = db.Column(db.Integer, ForeignKey(user.id), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    price = db.Column(db.DECIMAL(5,2), nullable=False)
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

# Create the database and table when the app starts
with app.app_context():  # Use the app context to perjson actions within the Flask application
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
        userData = user.query.filter(user.username == loginInfo['username']).first()

        if(userData is not None):
            if(loginInfo['pword'] == userData.pword):
                session['username'] = loginInfo['username']
                session['userID'] = userData.id
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
        adminData = admin.query.filter(admin.username == loginInfo['username']).first()

        if(adminData is not None):
            if(loginInfo['pword'] == adminData.pword):
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
            return jsonify({'error': 'Missing json'}), 400
        if(accountInfo['username'] is None):
            return jsonify({'error': 'Missing username'}), 400
        if(accountInfo['pword'] is None):
            return jsonify({'error': 'Missing password'}), 400
        if(accountInfo['address'] is None):
            return jsonify({'error': 'Missing address'}), 400
        if(accountInfo['email'] is None):
            return jsonify({'error': 'Missing email'}), 400
        if validate_email(accountInfo['email']) is None:
            return jsonify({'error': 'Invalid email'}), 400

        newUser = user(accountInfo['username'], accountInfo['pword'], accountInfo['address'], accountInfo['email']) # password should *NEVER* be stored in plaintext in a real production environment but im just trying to get it done :skull:
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
        price = Decimal(priceStr)
        return True
    except:
        return False

@app.route('/create', methods=['POST'])
def create():
    productInfo = request.form
    if ValidatePrice(productInfo['price']) is False:
        return jsonify({'error': 'could not convert string to decimal'}), 400

    if productInfo['description'] is None:
        desc = ""
    else:
        desc = productInfo['description']

    newProduct = inventory(productInfo['productname'], session['userID'], desc, productInfo['price'], productInfo['quantity'])
    db.session.add(newProduct)
    db.session.commit()
    return jsonify(newProduct.serialize()), 201

@app.route('/admincreate', methods=['POST'])
def admincreate():
    productInfo = request.form
    if ValidatePrice(productInfo['price']) is False:
        return jsonify({'error': 'could not convert string to decimal'}), 400

    if 'description' not in productInfo:
        desc = ""
    else:
        desc = productInfo['description']

    newProduct = inventory(productInfo['productname'], productInfo['userid'], desc, productInfo['price'], productInfo['quantity'])
    db.session.add(newProduct)
    db.session.commit()
    return jsonify(newProduct.serialize()), 201

@app.route('/read', methods=['GET'])
def read():
    productID = request.form['itemid']
    product = inventory.query.get(productID)
    if product is None:
        return jsonify({'error': 'no such product exists'}), 404
    if product.userID != session['userID']:
        return jsonify({'error': 'unauthorized'}), 401
    return product.serialize()

@app.route('/adminread', methods=['GET'])
def adminread():
    productID = request.form['itemid']
    product = inventory.query.get(productID)
    if product is None:
        return jsonify({'error': 'no such product exists'}), 404
    return product.serialize()

@app.route('/readall', methods=['GET'])
def readall():
    products = inventory.query.filter(inventory.userID == session['userID'])
    return [product.serialize() for product in products]

@app.route('/adminreadall', methods=['GET'])
def adminreadall():
    products = inventory.query.all()
    return [product.serialize() for product in products]

@app.route('/update', methods=['PUT'])
def update():
    productInfo = request.form
    product = inventory.query.get(productInfo['itemid'])
    if product is None:
        return jsonify({'error': 'no product with this id'}), 404
    if product.userID != session['userID']:
        return jsonify({'error': 'unauthorized'}), 401
    if 'price' in productInfo and productInfo['price'] != "":
        if ValidatePrice(productInfo['price']) == False:
            return jsonify({'error': 'could not convert string to decimal'}), 400
        product.price = productInfo['price']
    if 'productname' in productInfo and productInfo['productname'] != "":
        product.productName = productInfo['productname']
    if 'quantity' in productInfo and productInfo['quantity'] != "":
        product.quantity = productInfo['quantity']
    if 'description' in productInfo and productInfo['description'] != "":
        product.description = productInfo['description']
        
    db.session.commit()
    return product.serialize(), 201

@app.route('/adminupdate', methods=['PUT'])
def adminupdate():
    productInfo = request.form
    product = inventory.query.get(productInfo['itemid'])
    if product is None:
        return jsonify({'error': 'no product with this id'}), 404
    if 'price' in productInfo and productInfo['price'] != "":
        if ValidatePrice(productInfo['price']) is False:
            return jsonify({'error': 'could not convert string to decimal'}), 400
        product.price = productInfo['price']
    if 'userid' in productInfo and productInfo['userid'] != "":
        product.userID = productInfo['userid']
    if 'productname' in productInfo and productInfo['productname'] != "":
        product.productName = productInfo['productname']
    if 'quantity' in productInfo and productInfo['quantity'] != "":
        product.quantity = productInfo['quantity']
    if 'description' in productInfo and productInfo['description'] != "":
        product.description = productInfo['description']
        
    db.session.commit()
    return product.serialize(), 201

@app.route('/delete', methods=['DELETE'])
def delete():
    productID = request.form['itemid']
    product = inventory.query.get(productID)
    if product is None:
        return jsonify({'error': 'no such product exists'}), 404
    if product.userID != session['userID']:
        return jsonify({'error': 'unauthorized'}), 401

    db.session.delete(product)
    db.session.commit()
    return jsonify({'info': 'successfully deleted'}), 200

@app.route('/admindelete', methods=['DELETE'])
def admindelete():
    productID = request.form['itemid']
    product = inventory.query.get(productID)
    if product is None:
        return jsonify({'error': 'no such product exists'}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({'info': 'successfully deleted'}), 200

# Error handler for 404 Not Found
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'page not found'}), 404  # Return JSON with error message and 404 status

# Error handler for 400 Bad Request
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'bad request'}), 400  # Return JSON with error message and 400 status

if __name__ == '__main__':
    app.run(debug=True, port=3000)