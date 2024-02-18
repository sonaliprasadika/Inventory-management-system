from flask import Flask, Response, jsonify, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

api = Api(app)
    
class StorageItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    location = db.Column(db.String(64), nullable=False )

    product = db.relationship("Product", back_populates="in_storage")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    handle = db.Column(db.String(64), nullable=False)
    weight = db.Column(db.Float, nullable = False)
    price = db.Column(db.Float, nullable=False)

    in_storage = db.relationship("StorageItem", back_populates="product")

# Define a function to create tables within the application context
def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()

# Call the function to create tables
create_tables()

    
class ProductCollection(Resource):
    def get(self):
        products = Product.query.all()
        product_list = []
        for product in products:
            product_dict = {
                "handle": product.handle,
                "weight": product.weight,
                "price": product.price
            }
            product_list.append(product_dict)
        return jsonify(product_list)

    def post(self):
        data = request.json
        if not data or 'handle' not in data:
            return {"message": "No input data provided"}, 400
        
        if (data['weight'] is not None and not isinstance(data['weight'], float)):
            return {"message": "Weight must be a float"}, 400
            
        if (data['price'] is not None and not isinstance(data['price'], float)):
            return {"message": "Price must be a float"}, 400

        handle = data['handle']
        existing_product = Product.query.filter_by(handle=handle).first()
        if existing_product:
            return {"error": "Handle already exists"}, 409
        try:
            product = Product(
                handle=data["handle"],
                weight=data["weight"],
                price=data["price"]
            )
            db.session.add(product)
            db.session.commit()
        except ValueError as e:
            return {"message": str(e)}, 400
        return Response(
            status=201, headers={"Location": api.url_for(ProductItem, handle=product.handle)}
        )
class ProductItem(Resource):
    
    def get(self):
        return Response(status=501)

api.add_resource(ProductCollection, "/api/products/")
api.add_resource(ProductItem, "/api/products/<handle>/")

if __name__ == "__main__":
    app.run(debug=True)
