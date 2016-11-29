from flask_sqlalchemy import SQLAlchemy 
from flask import Flask
from flask_table import Table, Col
from datetime import datetime

app = Flask(__name__)
app.debug = True
app.threaded = True
app.config['SECRET_KEY'] = 'development key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/JP_Project' #'mysql://test_user:asease@localhost/hw2'#
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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