from stem import Signal
from stem.control import Controller
import urllib2
import time
def _set_urlproxy():
    proxy_support = urllib2.ProxyHandler({'http':"127.0.01:8118"})
    opener = urllib2.build_opener(proxy_support)
    urllib2.install_opener(opener)

def new_ip ():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password="p709269")
        controller.signal(Signal.NEWNYM)
        time.sleep(controller.get_newnym_wait())

for i in range(0,10):
    new_ip()
    _set_urlproxy()
    print urllib2.urlopen("http://icanhazip.com").read()