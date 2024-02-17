from flask_restful import Resource
from flask import Flask, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)

class SensorCollection(Resource):

    def get(self):
        pass

    def post(self):
        if not request.json:
            abort(415)
            
        try:
            sensor = Sensor(
                name=request.json["name"],
                model=request.json["model"],
            )
            db.session.add(sensor)
            db.session.commit()
        except KeyError:
            abort(400)
        except IntegrityError:
            abort(409)
        
        return "", 201


class SensorItem(Resource):

    def get(self, sensor):
        pass

    def put(self, sensor):
        pass

    def delete(self, sensor):
        pass
    
    
api.add_resource(SensorCollection, "/api/sensors/")
api.add_resource(SensorItem, "/api/sensors/<sensor>/")