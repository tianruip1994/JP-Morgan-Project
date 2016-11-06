from flask_sqlalchemy import SQLAlchemy 
from flask import Flask, session, request, render_template, redirect
from flask_table import Table, Col
from datetime import datetime
from flask_socketio import SocketIO, emit
from models import User #try to add more import to separate classes
import threading
import time
import urllib2
import json
import random

# Server API URLs
QUERY = "http://localhost:8080/query?id={}"
ORDER = "http://localhost:8080/order?id={}&side=sell&qty={}&price={}"

curPrice = 0
orderAvailable = False
priceLock = threading.Lock()
orderLock = threading.Lock()

ORDER_DISCOUNT = 5

import threading
import time
import sys

app = Flask(__name__)
app.debug = True
app.threaded = True
app.config['SECRET_KEY'] = 'development key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@localhost/JP_Project' #'mysql://test_user:asease@localhost/hw2'#
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app)

class Order(db.Model):
    __tablename__ = 'Order'
    order_id = db.Column(db.Integer, primary_key=True)
    totalVolume = db.Column(db.String(64))
    uid = db.Column(db.Integer)#, db.ForeignKey('user.uid'))
    time = db.Column(db.DateTime)
    suborderList = []

    def __init__(self, totalVolume, uid,time):
        self.time=time
        self.totalVolume = totalVolume
        self.uid = uid
    def __repr__(self):
        return '<Order %d>' % self.order_id
    def sellOrder(self):
        print(self.uid)
        print("in sellOrder")
        print(len(self.suborderList))
        sys.stdout.flush()
        while (len(self.suborderList)):
            sell = self.suborderList[0].sell()
            print("after sell")
            sys.stdout.flush()
            if (sell >= 0):
                del self.suborderList[0]
                self.totalVolume = self.totalVolume - sell
                numOfSlice = len(self.suborderList);
                # TODO what should we do if we cannot sell all of the suborders at last
                if (numOfSlice == 0):
                    numOfSlice = 1
                self.suborderList = SplitAlgorithm.tw(Order, numOfSlice)
            else:
                del self.suborderList[0]
            #-------------- ATTENTION -----------------
            #time interval between each sell
            time.sleep(10)


    #split function goes here---------

class Suborder(db.Model):
    __tablename__ = 'Suborder'
    suborder_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Float)
    time = db.Column(db.DateTime)
    volume = db.Column(db.Float)
    price = db.Column(db.Float)
    order_id = db.Column(db.Integer)#, db.ForeignKey('order.order_id'))
    def __init__(self, status, time, volume, price, order_id):
        self.status = status
        self.time = time
        self.volume = volume
        self.price = price
        self.order_id = order_id
    def sell(self):
        global curPrice
        # Attempt to execute a sell order.
        print("in sell")
        sys.stdout.flush()

        #-------------- ATTENTION -----------------
        # standard way to read curPrice
        priceLock.acquire()
        tmpPrice = curPrice
        priceLock.release()

        order_args = (self.volume, tmpPrice - ORDER_DISCOUNT)
        print "Executing 'sell' of {:,} @ {:,}".format(*order_args)
        url   = ORDER.format(random.random(), *order_args)
        order = json.loads(urllib2.urlopen(url).read())

        # Update the PnL if the order was filled.
        if order['avg_price'] > 0:
            price    = order['avg_price']
            notional = float(price * self.volume)
            print "Sold {:,} for ${:,}/share, ${:,} notional".format(self.volume, price, notional)
            self.status = 1
            self.price = price
        else:
            print "Unfilled order"
            self.status = 0

        self.time = datetime.now()
        db.session.add(self)
        db.session.commit()
        
        return -self.status


class SplitAlgorithm(object):
    @staticmethod
    def tw(order, numOfSlice):
        re = [order.totalVolume/numOfSlice] * (numOfSlice);
        remind = order.totalVolume % numOfSlice
        for i in range(0, remind):
            re[i] = re[i] + 1
        suborderList = []
        for i in range(0, numOfSlice):
            suborderList.append(Suborder(0, datetime.now(), re[i], 0, order.order_id))
        return suborderList


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

new_order = Order(-1,-1,datetime.utcnow())

@socketio.on('my event')
def showPrice(msg):
    print("msg:" + msg['data'])
    sys.stdout.flush()
    while True:
        priceLock.acquire()
        tmpPrice = curPrice
        priceLock.release()
        emit('resPrice', tmpPrice)
        time.sleep(1)

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
                return render_template("submitOrder.html")
                # return redirect('/userProfile')
        else:
            error = 'Oops! We cannot find this combination of username and password in our database.'
            context = dict(error=error)
            return render_template("login.html", **context)

@app.route('/createOrder')
def createOrder():
    return render_template("submitOrder.html")

@app.route('/submitOrder', methods=['POST'])
def submitOrder():
    global orderAvailable
    global new_order
    quantity = request.form['quantity']
    print(quantity)
    print(session['uid'])
    new_order = Order(quantity,session['uid'],datetime.utcnow())
    db.session.add(new_order)
    # split order
    # new_order.suborders = algo.two()
    db.session.commit()

    #-------------- ATTENTION -----------------
    #times in which the order will be sold
    new_order.suborderList = SplitAlgorithm.tw(new_order, 5)
    for i in range(0, len(new_order.suborderList)):
    	print(new_order.suborderList[i].volume)
    
    sys.stdout.flush()
    # create a new thread for the order
    orderAvailable = True
    return redirect('/userProfile')

def getOrderDetails(order_id):
    """Based on the user_ID, get list of orders that belongs to user from the database
    expect output: list[dict(information_from_database)]"""
    # orders = Order.query.join(User, User.uid==Order.uid).filter_by(uid=uid).all()#filter(Order.time>=datetime.today()).all()
    # order_ids=[]
    # # for o in orders:
    # #     order_ids.append(o.order_id)
    # # print(order_ids)
    # order_ids.append(orders[0].order_id)
    order = Order.query.filter_by(order_id=order_id).first()
    result = Suborder.query.filter_by(order_id=order_id).all()
    executedVolume = 0
    for r in result:
        executedVolume = executedVolume + r.volume
    totalVolume = order.totalVolume
    process = executedVolume * 100 / totalVolume
    remainingVolume = totalVolume - executedVolume
    return result, process, remainingVolume

def get_orders(uid):
    orders = Order.query.join(User, User.uid==Order.uid).filter_by(uid=uid).all()
    return orders

@app.route('/orderDetails', methods=['POST'])
def orderDetails():
    uid = session['uid']
    user = User.query.filter_by(uid=uid).first()
    order_id = request.form['order_id']
    # orders = Order.query.join(User, User.uid==Order.uid).filter_by(uid=uid).first()
    # order_id = orders.order_id
    # result = Suborder.query.filter_by(order_id=order_id).all()
    items,process,remainingVolume = getOrderDetails(order_id)
    table = ItemTable(items)
    if uid is not None:
        context = dict(user=user, items=items,process=process,remainingVolume=remainingVolume)
        return render_template('orderDetails.html', **context)
    else:
        error = 'Please login to view profile page.'
        context = dict(error=error)
        return render_template("login.html", **context)

@app.route('/userProfile')
def userProfile():
    uid = session['uid']
    user = User.query.filter_by(uid=uid).first()
    orders = get_orders(uid)
    context = dict(orders=orders,user=user)
    return render_template('profile.html', **context)

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


def getPrice():
    print "start get price from JP-server"
    # get price from JP-server continously.
    global curPrice
    while True:

        # Query the price once every 1 seconds.
        quote = json.loads(urllib2.urlopen(QUERY.format(random.random())).read())
        priceLock.acquire()
        curPrice = float(quote['top_bid']['price'])
        priceLock.release()
        #print "Quoted at %s" % curPrice
        sys.stdout.flush()

        time.sleep(1)

    print "stop get price from JP-server"

def checkAndSell():
    print "check and sell order"
    
    global orderAvailable
    global new_order
    while True:
        if orderAvailable:
            orderLock.acquire()
            tmpOrder = new_order
            orderLock.release()
            orderTread = threading.Thread(target = tmpOrder.sellOrder(), args = (), name = "newOrder")
            orderTread.start()

            orderAvailable = False

        time.sleep(1)

    print "stop check and sell order"



if __name__ == "__main__":
    getPriceFromJP = threading.Thread(target=getPrice, args=(), name="getPriceDaemon")
    getPriceFromJP.daemon = True
    getPriceFromJP.start()
    checkAndSellOrder = threading.Thread(target=checkAndSell, args=(), name="checkAndSellDaemon")
    checkAndSellOrder.daemon = True
    checkAndSellOrder.start()
    #app.run(debug=True, threaded=True)
    socketio.run(app)

