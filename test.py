from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Test(Base):
    __tablename__ = "test"
    
    id = Column(Integer, primary_key=True)
    test_test = Column(String)
    
def create_connection():
    engine = create_engine("postgresql://postgres:postgres@82.202.138.183:5432/postgres", echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    
    return Session(bind=engine)

session = create_connection()

test_row = session.query(Test).filter(Test.id == 1).first()
print(test_row.test_test)
session.close()