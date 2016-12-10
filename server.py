#from flask_socketio import SocketIO, emit
import threading
import time
import urllib2
import json
import random
import time
import sys
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session, request, render_template, redirect
from flask_table import Table, Col
from datetime import datetime


# exchange deadline
#exchangeDead = " 17:00:00"
#endTime = time.strftime("%Y-%m-%d", time.localtime()) + " 17:00:00";
endTime = time.strftime("%Y-%m-%d", time.localtime())+ " " + \
time.strftime("%H:%M:%S", time.localtime(time.time() + 20))
endTime = time.mktime(time.strptime(endTime, "%Y-%m-%d %H:%M:%S"))



# Server API URLs
QUERY = "http://localhost:8080/query?id={}"
ORDER = "http://localhost:8080/order?id={}&side=sell&qty={}&price={}"

curPrice = 0
orderAvailable = False
cancel = False
priceLock = threading.Lock()
orderLock = threading.Lock()

ORDER_DISCOUNT = 5



app = Flask(__name__)
app.debug = True
app.threaded = True
app.config['SECRET_KEY'] = 'development key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/JP_Project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#socketio = SocketIO(app)

class User(db.Model):
    __tablename__ = 'User'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(45), unique=True)
    password = db.Column(db.String(45))
    #orders = db.relationship('Order', backref='user.uid', lazy='joined')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username

class Order(db.Model):
    __tablename__ = 'Order'
    order_id = db.Column(db.Integer, primary_key=True)
    totalVolume = db.Column(db.String(64))
    uid = db.Column(db.Integer)#, db.ForeignKey('user.uid'))
    time = db.Column(db.DateTime)
    sliceNum = 5
    interval = 0
    suborderList = []

    def __init__(self, totalVolume, uid, curtime):
        self.time = curtime
        self.totalVolume = totalVolume
        self.uid = uid
    def __repr__(self):
        return '<Order %d>' % self.order_id
    def sellOrder(self):
        global cancel
        print self.uid
        print "in sellOrder"
        print len(self.suborderList)
        sys.stdout.flush()
        while len(self.suborderList):
            sell = self.suborderList[0].sell()
            print "after sell"
            sys.stdout.flush()
            #Handle unsold order
            if sell == 1:
                del self.suborderList[0]
                numOfSlice = len(self.suborderList)
                # TODO what should we do if we cannot sell all of the suborders at last
                if numOfSlice == 0:
                    numOfSlice = 1
                self.suborderList = SplitAlgorithm.tw(self)
            #Handle big order:
            elif sell == 2:
                self.sliceNum = self.sliceNum * 2
                self.suborderList = SplitAlgorithm.tw(self)
                print "new sliceNum = " + str(self.sliceNum)
                continue

            elif sell == 3:
                del self.suborderList[0]
                continue

            #Handle sold order
            else:
                self.totalVolume = self.totalVolume - self.suborderList[0].volume
                print self.totalVolume
                if self.totalVolume <= 0:
                    break
                self.sliceNum = self.sliceNum / 2
                if self.sliceNum == 0:
                    self.sliceNum = 1
                self.suborderList = SplitAlgorithm.tw(self)
            #-------------- ATTENTION -----------------
            #time interval between each sell
            #time.sleep(10)
            realInterval = self.interval
            if realInterval < 1:
                realInterval = 1
            time.sleep(realInterval)
        cancel = False

"""
split function goes here---------
"""
class Suborder(db.Model):
    __tablename__ = 'Suborder'
    suborder_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Float)
    time = db.Column(db.DateTime)
    volume = db.Column(db.Float)
    price = db.Column(db.Float)
    order_id = db.Column(db.Integer)#, db.ForeignKey('order.order_id'))
    def __init__(self, status, curtime, volume, price, order_id):
        self.status = status
        self.time = curtime
        self.volume = volume
        self.price = price
        self.order_id = order_id
    def sell(self):
        global curPrice
        global cancel
        # Attempt to execute a sell order.
        print "in sell"
        sys.stdout.flush()

        #-------------- ATTENTION -----------------
        # standard way to read curPrice
        priceLock.acquire()
        tmpPrice = curPrice
        priceLock.release()

        order_args = (self.volume, tmpPrice - ORDER_DISCOUNT)
        print cancel
        if cancel == True:
            print "order canceled."
            self.status = 3
            self.price = None
            db.session.add(self)
            db.session.commit()
            return self.status

        print "Executing 'sell' of {:,} @ {:,}".format(*order_args)
        url = ORDER.format(random.random(), *order_args)
        try:
            order = json.loads(urllib2.urlopen(url).read())
        except ValueError:
            print "order is too big to sell"
            #big order
            quote = json.loads(urllib2.urlopen(QUERY.format(random.random())).read())
            print quote
            self.time = quote['timestamp']
            self.status = 2
        else:
            # Update the PnL if the order was filled.
            if order['avg_price'] > 0:
                price = order['avg_price']
                notional = float(price * self.volume)
                print "Sold {:,} for ${:,}/share, ${:,} notional".format(self.volume,\
                    price, notional)
                #sold order
                self.status = 0
                self.price = price
            else:
                #unsold order
                print "Unfilled order"
                self.status = 1
                self.price = None

            self.time = order['timestamp']

        db.session.add(self)
        db.session.commit()

        return self.status

"""
Use an algorithm to split order 
"""
class SplitAlgorithm(object):
    @staticmethod
    def tw(order):
        numOfSlice = order.sliceNum
        re = [order.totalVolume/numOfSlice] * (numOfSlice)
        remind = order.totalVolume % numOfSlice
        for i in range(0, remind):
            re[i] = re[i] + 1
        suborderList = []
        for i in range(0, numOfSlice):
            suborderList.append(Suborder(0, datetime.now(), re[i], 0, order.order_id))
        order.interval = (endTime - time.time()) / numOfSlice
        print "interval = " + str(order.interval)
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

new_order = Order(-1, -1, datetime.utcnow())

# @socketio.on('my event')
# def showPrice(msg):
#     print("msg:" + msg['data'])
#     sys.stdout.flush()
#     while True:
#         priceLock.acquire()
#         tmpPrice = curPrice
#         priceLock.release()
#         emit('resPrice', tmpPrice)
#         time.sleep(1)

@app.route('/')
def index():
    if len(session) == 0:
        return render_template("login.html")
    else:
        return redirect('/userProfile')

@app.route('/loginpage')
def loginPage():
    return render_template("login.html")


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    if len(username) > 45 or len(password) > 45:
        error = 'The maximum length for username and password is 45 characters.'
        context = dict(error=error)
        return render_template("login.html", **context)
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
    orders = Order.query.join(User, User.uid ==\
        Order.uid).filter_by(uid=uid).first()
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
            # print(submit)
            context = dict(user=user)
            # return render_template('profile.html', **context)
            if submit:
                return redirect('/userProfile')
            else:
                return render_template("submitOrder.html")
                # return redirect('/userProfile')
        else:
            error = 'Oops! We cannot find this combination of \
            username and password in our database.'
            context = dict(error=error)
            return render_template("login.html", **context)

@app.route('/createOrder')
def createOrder():
    return render_template("submitOrder.html")

@app.route('/submitOrder', methods=['POST'])
def submitOrder():
    global orderAvailable
    global new_order
    volume = request.form['volume']
    if volume.isdigit() and int(volume) > 0 and int(volume) < 2147483647:
        quote = json.loads(urllib2.urlopen(QUERY.format(random.random())).read())
        new_order = Order(volume, session['uid'], quote['timestamp'])
        db.session.add(new_order)
        # split order
        # new_order.suborders = algo.two()
        db.session.commit()
        #times in which the order will be sold
        new_order.suborderList = SplitAlgorithm.tw(new_order)
        # for i in range(0, len(new_order.suborderList)):
    	   # print(new_order.suborderList[i].volume)

        sys.stdout.flush()
        # create a new thread for the order
        orderAvailable = True
        #return to order page
        uid = session['uid']
        user = User.query.filter_by(uid=uid).first()
        items, process, remainingVolume = getOrderDetails(new_order.order_id)
        order_id = new_order.order_id
        context = dict(user=user, items=items, process=process, remainingVolume=remainingVolume,\
            itemsLen=len(items), order_id=order_id)
        return render_template('orderDetails.html', **context)
    else:
        error = 'Please enter a positive integer for volume.'
        context = dict(error=error)
        return render_template("submitOrder.html", **context)

def getOrderDetails(order_id):
    """Based on the user_ID, get list of orders that belongs to user from the database
    expect output: list[dict(information_from_database)]"""
    order = Order.query.filter_by(order_id=order_id).first()
    result = Suborder.query.filter_by(order_id=order_id).order_by(Suborder.time.desc()).all()
    executedVolume = 0
    for r in result:
        if r.status == 0:
            executedVolume = executedVolume + r.volume
    totalVolume = order.totalVolume
    process = executedVolume * 100 / totalVolume
    remainingVolume = totalVolume - executedVolume
    return result, process, remainingVolume

def get_orders(uid):
    orders = Order.query.join(User, User.uid == \
        Order.uid).filter_by(uid=uid).order_by(Order.time.desc()).all()
    return orders

@app.route('/orderDetails', methods=['POST'])
def orderDetails():
    uid = session['uid']
    user = User.query.filter_by(uid=uid).first()
    order_id = request.form['order_id']
    # orders = Order.query.join(User, User.uid==Order.uid).filter_by(uid=uid).first()
    # order_id = orders.order_id
    # result = Suborder.query.filter_by(order_id=order_id).all()
    items, process, remainingVolume = getOrderDetails(order_id)
    table = ItemTable(items)
    if uid is not None:
        context = dict(user=user, items=items, process=process, remainingVolume=remainingVolume,\
            itemsLen=len(items), order_id=order_id)
        return render_template('orderDetails.html', **context)
    else:
        error = 'Please login to view profile page.'
        context = dict(error=error)
        return render_template("login.html", **context)

@app.route('/orderCancel', methods=['POST'])
def ordercancel():
    global orderAvailable
    global cancel
    global new_order
    uid = session['uid']
    user = User.query.filter_by(uid=uid).first()
    # now only one order need to be considered
    order_id = request.form['order_id']
    if int(order_id) == int(new_order.order_id):
        orderAvailable = False
        cancel = True
    return redirect('/userProfile')


@app.route('/userProfile')
def userProfile():
    uid = session['uid']
    user = User.query.filter_by(uid=uid).first()
    orders = get_orders(uid)
    new_orders = list()
    i = 1
    for order in orders:
        print order.time
        process = getOrderDetails(order.order_id)[1]
        new_orders.append((order, process, i))
        i += 1
    context = dict(orders=new_orders, user=user)
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
        error = 'Oops! We cannot find this username in our database. \
        Make sure the username is registered.'
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
            orderTread = threading.Thread(target=tmpOrder.sellOrder(), args=(), name="newOrder")
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
    app.run(debug=True)
    #app.run(debug=True, threaded=True)
    #socketio.run(app)
