from django.apps import AppConfig
from .views import mongo_connect

class MongodbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mongodb'
    mongo_db = None

    def ready(self):
        # Establish MongoDB connection on server start
        mongo_db = mongo_connect()
        print(f"Connected to MongoDB database: {mongo_db.name}")