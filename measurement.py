import json
from datetime import datetime
from flask import Flask, Response, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event
from jsonschema import validate, ValidationError, FormatChecker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from werkzeug.routing import BaseConverter

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)

deployments = db.Table("deployments",
    db.Column("deployment_id", db.Integer, db.ForeignKey("deployment.id"), primary_key=True),
    db.Column("sensor_id", db.Integer, db.ForeignKey("sensor.id"), primary_key=True)
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    altitude = db.Column(db.Float, nullable=True)
    description=db.Column(db.String(256), nullable=True)
    
    sensor = db.relationship("Sensor", back_populates="location", uselist=False)

class Deployment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=True)
    end = db.Column(db.DateTime, nullable=True)
    name = db.Column(db.String(128), nullable=False)
    
    sensors = db.relationship("Sensor", secondary=deployments, back_populates="deployments")

class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    model = db.Column(db.String(128), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"), unique=True)
    
    location = db.relationship("Location", back_populates="sensor")
    measurements = db.relationship("Measurement", back_populates="sensor")
    deployments = db.relationship("Deployment", secondary=deployments, back_populates="sensors")
    
class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey("sensor.id", ondelete="SET NULL"))
    value = db.Column(db.Float, nullable=False)
    time = db.Column(db.DateTime, nullable=False)
        
    sensor = db.relationship("Sensor", back_populates="measurements")

    def deserialize(self, doc):
        self.value = doc.get("value")
        timestamp_str = doc.get('time')
        if timestamp_str:
            self.time = datetime.fromisoformat(timestamp_str)

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["time", "value"]
        }
        props = schema["properties"] = {}
        props["time"] = {
            "description": "Measurd time",
            "type": "string",
            "format": "date-time"
        }
        props["value"] = {
            "description": "Measurement",
            "type": "number"
        }
        return schema
    
class MeasurementCollection(Resource):
    def get(self,sensor):
        pass

    def post(self,sensor):
        if request.headers["Content-Type"] != "application/json":
            raise UnsupportedMediaType("Unsupported media type")
        
        try:
            data = request.get_json()
            validate(data, Measurement.json_schema(), format_checker=FormatChecker())
            new_measurement = Measurement()
            new_measurement.deserialize(data)
            new_measurement.sensor = sensor

            db.session.add(new_measurement)
            db.session.commit()
        except ValidationError as e:
            raise BadRequest(str(e)) from e  
        except IntegrityError as e:
            raise Conflict(409, description=f"'{request.json['name']}' already exists."
            ) from e 

        measurement_url = api.url_for(
            MeasurementItem,
            sensor=sensor.name,
            measurement=new_measurement.id
        )

        return Response(status=201, headers={"Location": measurement_url})
    
class MeasurementItem(Resource):
    def delete(self, sensor, measurement):
        pass

class SensorConverter(BaseConverter):    
    def to_python(self, value):
        db_sensor = Sensor.query.filter_by(name=value).first()
        if db_sensor is None:
            raise NotFound
        return db_sensor
        
    def to_url(self, value):
        return value

class SensorCollection(Resource):

    def get(self):
        response_data = []
        sensors = Sensor.query.all()
        for sensor in sensors:
            response_data.append([sensor.name, sensor.model])       
        return json.dumps(response_data)


    def post(self):
        if not request.json:
            return "", 415            
        try:
            sensor = Sensor(
                name=request.json["name"],
                model=request.json["model"]
            )
            print(Sensor)
            db.session.add(sensor)
            db.session.commit()
        except KeyError:
            return "", 400
        except IntegrityError:
            return "", 409
        
        return "", 201

class SensorItem(Resource):

    def get(self, sensor):
        pass

    def put(self, sensor):
        pass

    def delete(self, sensor):
        pass

with app.app_context():
    db.drop_all()
    db.create_all()

app.url_map.converters["sensor"] = SensorConverter

api.add_resource(SensorCollection, "/api/sensors/")
api.add_resource(SensorItem, "/api/sensors/<sensor>/")
api.add_resource(MeasurementCollection, "/api/sensors/<sensor:sensor>/measurements/")
api.add_resource(MeasurementItem, "/api/sensors/<sensor:sensor>/measurements/<int:measurement>/")
