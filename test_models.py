from models import engine, Base, Session

Base.metadata.create_all(engine)
session = Session()
session.close()
print("База создана успешно")