from django.apps import AppConfig
from .views import mongo_connect

class MongodbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mongodb'
