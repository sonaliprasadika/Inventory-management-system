from flask import Flask
from flask_restful import Api
from resources.Product import ProductCollection, ProductItem
from flask import Blueprint
from resources.Product import init_db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# Initialize SQLAlchemy with the Flask app
init_db(app)


# Rest of your app setup
api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

# Register resources
api.add_resource(ProductCollection, "/products")
api.add_resource(ProductItem, "/products/<string:handle>/")

# Register blueprint with Flask app
app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run(debug=True)
