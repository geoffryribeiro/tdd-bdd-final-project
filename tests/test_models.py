import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres")

class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        db.session.close()

    def setUp(self):
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    def test_create_a_product(self):
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.available, True)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)

    def test_read_a_product(self):
        product = ProductFactory()
        product.create()
        found = Product.find(product.id)
        self.assertEqual(found.id, product.id)

    def test_update_a_product(self):
        product = ProductFactory()
        product.create()
        product.description = "Updated description"
        product.update()
        updated = Product.find(product.id)
        self.assertEqual(updated.description, "Updated description")

    def test_update_without_id_raises_error(self):
        product = Product(name="TV", description="Smart TV", price=999.99, available=True, category=Category.HOUSEWARES)
        with self.assertRaises(DataValidationError) as context:
            product.update()
        self.assertEqual(str(context.exception), "Update called with empty ID field")

    def test_delete_a_product(self):
        product = ProductFactory()
        product.create()
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_serialize_product(self):
        product = ProductFactory()
        result = product.serialize()
        self.assertEqual(result["name"], product.name)
        self.assertEqual(result["description"], product.description)
        self.assertEqual(result["price"], str(product.price))
        self.assertEqual(result["available"], product.available)
        self.assertEqual(result["category"], product.category.name)

    def test_deserialize_valid_product(self):
        data = {
            "name": "Notebook",
            "description": "Ultrabook Dell",
            "price": "4800.00",
            "available": True,
            "category": "TOOLS"
        }
        product = Product()
        product.deserialize(data)
        self.assertEqual(product.name, "Notebook")
        self.assertEqual(product.price, Decimal("4800.00"))
        self.assertEqual(product.category, Category.TOOLS)

    def test_deserialize_invalid_boolean(self):
        data = {
            "name": "Notebook",
            "description": "Ultrabook Dell",
            "price": "4800.00",
            "available": "yes",  # inválido!
            "category": "TOOLS"
        }
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_deserialize_missing_field(self):
        data = {
            "name": "Notebook",
            "price": "4800.00",
            "available": True,
            "category": "TOOLS"
        }  # faltando 'description'
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_deserialize_type_error(self):
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(None)

    def test_find_by_name(self):
        products = ProductFactory.create_batch(3)
        for p in products:
            p.create()
        name = products[0].name
        found = Product.find_by_name(name)
        self.assertTrue(all(p.name == name for p in found))

    def test_find_by_availability_true(self):
        products = ProductFactory.create_batch(4)
        for p in products:
            p.available = True
            p.create()
        found = Product.find_by_availability(True)
        self.assertTrue(all(p.available for p in found))

    def test_find_by_availability_false(self):
        products = ProductFactory.create_batch(4)
        for p in products:
            p.available = False
            p.create()
        found = Product.find_by_availability(False)
        self.assertEqual(found.count(), 4)
        for p in found:
            self.assertFalse(p.available)

    def test_find_by_category(self):
        products = ProductFactory.create_batch(5)
        for p in products:
            p.create()
        category = products[0].category
        found = Product.find_by_category(category)
        self.assertTrue(all(p.category == category for p in found))

    def test_find_by_unknown_category(self):
        product = ProductFactory(category=Category.UNKNOWN)
        product.create()
        found = Product.find_by_category(Category.UNKNOWN)
        self.assertGreaterEqual(found.count(), 1)
        for item in found:
            self.assertEqual(item.category, Category.UNKNOWN)
