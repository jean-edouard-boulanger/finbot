from datetime import datetime
from flask import jsonify
from pydantic import BaseModel
from finbot.apps.finbotwsrv.finbotwsrv import app


class TestModel(BaseModel):
    d: datetime


with app.test_request_context():
    v = TestModel(d=datetime.now())
    print(jsonify(v.dict()).get_data())
