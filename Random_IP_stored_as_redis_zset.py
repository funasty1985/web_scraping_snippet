# This is a script for randomly select an IP from the proxy sorted set
from redis import StrictRedis
import random
import time

class RandomProxyMiddelware (object):

    def __init__(self):
        self.redis = StrictRedis(port=6379)
        # delete expired IP
        tm = time.time()
        self.redis.zremrangebyscore('proxy', '-inf', tm)

    def process_request (self, request, spider):
        min_score = self.redis.zrange('proxy', 0, 0, withscores=True)[0][1] - 1
        max_score = self.redis.zrange('proxy', -1, -1, withscores=True)[0][1] + 1
        rand = random.randrange(min_score, max_score, 1)
        # the redis-cli commond is ZRANGEBYSCORE 'PROXY' rand max_score LIMIT rand 1
        ip = self.redis.zrangebyscore('proxy', rand, max_score, start=rand, num=1)
        request.meta['proxy'] = ip