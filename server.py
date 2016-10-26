from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session, request, render_template, redirect
from flask_table import Table, Col

import threading
import time
import sys

priceLock = threading.Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'development key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@localhost/JP_Project' #'mysql://test_user:asease@localhost/hw2'#
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'User'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(45), unique=True)
    password = db.Column(db.String(45))
    # orders = db.relationship('Order', backref='user', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username

class Order(db.Model):
    __tablename__ = 'Order'
    order_id = db.Column(db.Integer, primary_key=True)
    totalVolume = db.Column(db.Integer)
    uid = db.Column(db.Integer)#, db.ForeignKey('user.uid'))
    suborderList = []
    def __init__(self, totalVolume, uid):
        self.totalVolume = totalVolume
        self.uid = uid
    def __repr__(self):
        return '<Order %d>' % self.order_id
    def sellOrder():
    	while (len(subOrderList)):
    		sell = suborderList[0].sell()
    		if (sell >= 0):
    			del suborderList[0]
    			totalVolume = totalVolume - sell
    			numOfSlice = len(subOrderList);
    			# TODO what should we do if we cannot sell all of the suborders at last
    			if (numOfSlice == 0):
    				numOfSlice = 1
    			subOrderList = SplitAlgorithm.tw(Order, numOfSlice)
    		else:
    			del suborderList[0]
    		sleep(5)





    #split function goes here---------

class Suborder(db.Model):
    __tablename__ = 'Suborder'
    suborder_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Float)
    time = db.Column(db.DateTime)
    volume = db.Column(db.Float)
    price = db.Column(db.Float)
    order_id = db.Column(db.Integer)#, db.ForeignKey('order.order_id'))
    def __init__(self, status, time, volume, price):
        self.status = status;
        self.time = time;
        self.volume = volume;
        self.price = price;
    #execute suborder function goes here--------


class SplitAlgorithm(object):
	@staticmethod
	def tw(order, numOfSlice):
		re = [order.totalVolume/numOfSlice] * (numOfSlice);
		remind = order.totalVolume % numOfSlice
		for i in range(0, remind):
			re[i] = re[i] + 1
		return re


class ItemTable(Table):
    suborder_id = Col('Order_ID')
    status = Col('Status')
    volume = Col('Description')
    price = Col('Price')

class Item(object):
    def __init__(self, order_Id, status, quantity, price):
        self.order_Id = order_id
        self.status = status
        self.quantity = volume
        self.price = price

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/loginpage')
def loginPage():
    return render_template("login.html")


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    checkUser = User.query.filter_by(username=username).first()
    if checkUser is not None:
        error = 'The username you typed is already used. Please choose another one.'
        context = dict(error=error)
        return render_template("login.html", **context)
    else:
        new_user = User(username, password)
        db.session.add(new_user)
        db.session.commit()
        msg = 'You\'ve successfully registered!'
        context = dict(msg=msg)
        return render_template("login.html", **context)

def is_order_submit(uid):
    """Based on the user_ID, check whether user has order or not
    return true is user had submitted order"""
    #need to be filled
    orders = Order.query.join(User, User.uid==Order.uid).filter_by(uid=uid).first()
    return not orders == None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        error = None
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(
            username=username, password=password).first()
        if user is not None:
            session['uid'] = user.uid
            submit = is_order_submit(user.uid)
            print(submit)
            context = dict(user=user)
            # return render_template('profile.html', **context)
            if submit:
                return redirect('/userProfile')
            else:
                return render_template("submitOrder.html", **context)
                # return redirect('/userProfile')
        else:
            error = 'Oops! We cannot find this combination of username and password in our database.'
            context = dict(error=error)
            return render_template("login.html", **context)

@app.route('/submitOrder', methods=['POST'])
def submitOrder():
    quantity = request.form['quantity']
    print(quantity)
    print(session['uid'])
    new_order = Order(quantity,session['uid'])
    db.session.add(new_order)
    db.session.commit()
    new_order.subOrderList = SplitAlgorithm.tw(new_order,10)
    print(new_order.subOrderList)
    print("hello")
    sys.stdout.flush()
    # create a new thread for the order
    orderTread = threading.Thread(target = new_order.sellOrder())
    return render_template("submitOrder.html")

def get_items(uid):
    """Based on the user_ID, get list of orders that belongs to user from the database
    expect output: list[dict(information_from_database)]"""
    orders = Order.query.join(User, User.uid==Order.uid).filter_by(uid=uid).first()
    order_id = orders.order_id
    result = Suborder.query.filter_by(order_id=order_id).all()
    return result

@app.route('/userProfile')
def userProfile():
    uid = session['uid']
    user = User.query.filter_by(uid=uid).first()
    # orders = Order.query.join(User, User.uid==Order.uid).filter_by(uid=uid).first()
    # order_id = orders.order_id
    # result = Suborder.query.filter_by(order_id=order_id).all()
    items = get_items(uid)
    print(items)
    table = ItemTable(items)
    if user is not None:
        context = dict(user=user)
        print("context")
        print(context)
        return render_template('profile.html', table=table, **context)
    else:
        error = 'Please login to view profile page.'
        context['status'] = True
        context['quantity'] = 20
        context = dict(error=error)
        return render_template("index.html", **context)

@app.route('/forgotPassword')
def forgotPassword():
    return render_template("forgotPassword.html")


@app.route('/modifyPassword', methods=['POST'])
def modifyPassword():
    username = request.form['username']
    password = request.form['password']
    user_query = User.query.filter_by(username=username).first()
    if user_query is None:
        error = 'Oops! We cannot find this username in our database. Make sure the username is registered.'
        context = dict(error=error)
        return render_template("login.html", **context)
    else:
        user_query.password = password
        db.session.commit()
        msg = 'You\'ve successfully changed your password!'
        context = dict(msg=msg)
        return render_template("login.html", **context)


@app.route('/signout')
def signout():
    session.pop('uid', None)
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
