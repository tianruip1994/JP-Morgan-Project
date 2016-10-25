from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session, request, render_template, redirect

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
    #orders = db.relationship('Order', backref='user', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username

class Order(db.Model):
    __tablename__ = 'Order'
    order_id = db.Column(db.Integer, primary_key=True)
    totalVolume = db.Column(db.Integer)
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'))

    def __init__(self, totalVolume):
        self.totalVolume = totalVolume
    def __repr__(self):
        return '<Order %d>' % self.order_id
    #split function goes here---------

class Suborder(db.Model):
    __tablename__ = 'Suborder'
    suborder_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Float)
    time = db.Column(db.DateTime)
    volume = db.Column(db.Float)
    price = db.Column(db.Float)
    order_id = db.Column(db.Integer)
    def __init__(self, status, time, volume, price):
        self.status = status;
        self.time = time;
        self.volume = volume;
        self.price = price;
    #execute suborder function goes here--------

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
            context = dict(user=user)
            return redirect('/userProfile')
        else:
            error = 'Oops! We cannot find this combination of username and password in our database.'
            context = dict(error=error)
            return render_template("login.html", **context)


@app.route('/userProfile')
def userProfile():
    uid = session['uid']
    user = User.query.filter_by(uid=uid).first()
    orders = Order.query.join(User, User.uid==Order.uid).filter_by(uid=uid).first()
    order_id = orders.order_id
    result = Suborder.query.filter_by(order_id=order_id).all()
    if user is not None:
        context = dict(user=user,result=result)
        return render_template('profile.html', **context)
    else:
        error = 'Please login to view profile page.'
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
