class HashMap(object):

    def __init__(self, m, seed):
        """
        :param m: the number of bit in a boom filter
        :param seed: the iteration of the number of hash number desired , connection to BLOOMFILTER_HASH_NUMBER
        """
        self.m = m
        self.seed = seed

    def hash(self, value):
        """
        Hash function
        :param value: input string going to be hashed
        :return: Hash value
        """

        ret = 0
        for i in range(len(value)):
            ret += self.seed * ret + ord(value[i])
        return (self.m - 1) & ret
        # & is the bitwise operator , comparing the bits from two input and return the '1'
        # in their common position, and returning the corresponding decimal value
        # e.g self.m is 2^30 where is binary is 1+(30 # of zero) , 2^30-1 's binary is 30 # of '1'


# the number of hash numbers desired to generate from the input string
BLOOMFILTER_HASH_NUMBER = 6
# the number of bit in the bloom filter
BLOOMFILTER_BIT = 30


class BloomFilter(object):

    def __init__(self, server, key='bloomfilters', bit=BLOOMFILTER_BIT, hash_number=BLOOMFILTER_HASH_NUMBER):
        """
        :param server: the address of the redis server
        :param key: the key of the bloom filter in the redis db
        :param bit: the number of bit in the bloom filter
        :param hash_number: the number of hash numbers desired to generate from the input string
        """
        self.m = 1 << bit  # << is a bitwise operation , decimal 1 is convert to binary 1 and left shift bin number of position, 2^30
        self.seeds = range(hash_number)
        self.server = server
        self.maps = [HashMap(self.m, seed) for seed in
                     self.seeds]  # six HashMap objects with seed para from 1 to 6 is generated by default
        self.key = key

    def exists(self, value):
        """
        determine if a input string is in the Bloom filter
        :param value:
        :return:
        """
        if not value:
            return False
        exist = True
        for map in self.maps:  # recall self.map is a list of HaspMap object and each of them has different self.seed value and can call hash method
            offset = map.hash(value)
            exist = exist & self.server.getbit(self.key, offset)
            # getbit is a method of StrictRedis class object which use to examine bitset with self.key as key, offset is the position
            # of the bitset , it will return true if the position is set to one
        return exist

    def insert(self, value):

        for f in self.maps:
            offset = f.hash(value)
            self.server.setbit(self.key, offset, 1)


# the following part is the integration of Bloom filter into a scrapy middleware

from redis import StrictRedis
from redis_bloomfilter import BloomFilter
from scrapy.utils.request import request_fingerprint # crawler will save the fingerprint of each url scraped , note that it is a method
from scrapy.dupefilters import BaseDupeFilter
import logging


class RedisBloomDupefilter(BaseDupeFilter):

    def __int__(self, port, db, key, bit, hash_number):
        self.redis = StrictRedis(port=port, db=db)
        self.key = key
        self.bit = bit
        self.hash_number = hash_number
        self.bf = BloomFilter(self.redis, key, bit, hash_number)
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_settings(cls, settings):
        redis_port = settings.get('REDIS_PORT')
        redis_db = settings.get('REDIS_DUP_DB')
        redis_key = settings.get('REDIS_KEY')
        bit = settings.get('BLOOMFILTER_BIT')
        hash_number = settings.get('BLOOMFILTER_HASH_NUMBER')

        return cls(redis_port, redis_db, redis_key, bit, hash_number)

    def request_seen(self, request):
        fp = request_fingerprint(request)
        if self.bf.exists(fp):  # bf is a object of BloomFilter
            return True

        self.bf.insert(fp)
        return False

    def log(self, request, spider):
        if self.debug:
            msg = "Filtered duplicate request: %(request)s"
            self.logger.debug(msg, {'request': request}, extra={'spider': spider})
        elif self.logdupes:
            msg = ("Filtered duplicate request: %(request)s"
                   " - no more duplicates will be shown"
                   " (see DUPEFILTER_DEBUG to show all duplicates)")
            self.logger.debug(msg, {'request': request}, extra={'spider': spider})
            self.logdupes = False

        spider.crawler.stats.inc_value('dupefilter/filtered', spider=spider)


# at setting.py put down the following
# DUPEFILTER_CLASS = 'etsy_crawler.dupefilter.RedisBloomDupefilter' this is taking a instance of etsy_crawler and the script is stored after the etsy_crawler folder and called dupeilter 
# REDIS_DUP_DB = 0
# REDIS_PORT = 6379
# REDIS_KEY = 'Bloom_Filter'
# BLOOMFILTER_BIT = 30
# BLOOMFILTER_HASH_NUMBER = 6
