import redis
import os
from dotenv import load_dotenv

load_dotenv()

def redis_connect():
    redis_client = redis.Redis(host=os.environ.get('REDIS_HOST'), port=os.environ.get('REDIS_PORT'), db=os.environ.get('REDIS_DB'))
    return redis_client