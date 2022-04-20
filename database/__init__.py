from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from chadbox import app
import os

db_path = os.path.join(os.path.dirname(__file__), '../db.sqlite3')
db_uri = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ma = Marshmallow(app)

import database.models

db.create_all()
db.session.commit()
