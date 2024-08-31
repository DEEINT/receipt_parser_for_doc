from main import app
from main import db

with app.app_context(): 
    db.create_all() 