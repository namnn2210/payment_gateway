import redis
import os
from dotenv import load_dotenv

load_dotenv()

def redis_connect(db):
    redis_client = redis.Redis(host=os.environ.get('REDIS_HOST'), port=os.environ.get('REDIS_PORT'), password=os.environ.get('REDIS_PASSWORD'), db=db)
    return redis_client