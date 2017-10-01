from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import sys
import datetime


Base = declarative_base()

class FeedResult(Base):
    __tablename__= 'feed'

    id = Column(String, primary_key=True)
    feed_type = Column(String(250), nullable=False)
    date = Column(String, nullable=False)

engine = create_engine('sqlite:///amazon.db')
Base.metadata.create_all(engine)
