from flask import Flask
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


from app import views, database