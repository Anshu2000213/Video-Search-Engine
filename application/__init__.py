from flask import Flask, render_template, session
# from flask_pymongo import PyMongo
from neo4j import GraphDatabase
from flask_mysqldb import MySQL
import pymongo

app = Flask(__name__)
app.config["SECRET_KEY"] = 'd96cc265c99b01676d111a34d73a233e98925c00'
api_key = "AIzaSyCZrOkHAf1y5p_q3YwT11uecdYM-nKaois"

# MongoDB connection setup
conn = "mongodb+srv://mangal7:mongo@youtube.nsvixhb.mongodb.net/"
client = pymongo.MongoClient(conn, serverSelectionTimeoutMS=5000)
db = client['youtube']

username = 'neo4j'
pwd = 'cloud-applicants-pops'
uri = 'bolt://3.238.153.3:7687'

# Create a Neo4j driver
neo_driver = GraphDatabase.driver(uri=uri, auth=(username, pwd))

app.config['MYSQL_HOST'] = 'sql12.freesqldatabase.com'
app.config['MYSQL_USER'] = 'sql12668492'
app.config['MYSQL_PASSWORD'] = 'BN4lEIj3TP'
app.config['MYSQL_DB'] = 'sql12668492'
app.config['MYSQL_PORT'] = 3306
mysql = MySQL(app)

print(db)
print(neo_driver)
print(mysql)

# if('videos_count' in session):
#     session['videos_count'] = 0
video_list = []

from application import routes