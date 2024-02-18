from flask import Flask
from flask_restful import Api
from resources.Product import ProductCollection, ProductItem

# Create Flask app
app = Flask(__name__)

# Create Flask-Restful Api object
api = Api(app)

# Register resources
api.add_resource(ProductCollection, "/api/products/")
api.add_resource(ProductItem, "/api/products/<handle>/")

# Register Blueprint
from flask import Blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")
api.init_app(api_bp)

# Register Blueprint route
@api_bp.route("/")
def index():
    return ""

# Register Blueprint in the app
app.register_blueprint(api_bp)

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)
