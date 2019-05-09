from urllib.request import urlopen 
from bs4 import BeautifulSoup

response = urlopen('http://www.useragentstring.com/pages/useragentstring.php?name=Chrome')
rss = BeautifulSoup (response.read(),"html.parser")

element_list = rss.select('#liste ul a')

UA_list = []
for i in element_list :
    s = str(i)
    soup = BeautifulSoup(s) # Beautiful Soup only recognize string 
    text = soup.text
    UA_list.append(text)    

print (UA_list)

