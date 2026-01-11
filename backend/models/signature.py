from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Signature(Base):
    __tablename__ = "signatures"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    hash = Column(String)
    signature = Column(String)
