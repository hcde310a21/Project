
import urllib.parse, urllib.request, urllib.error,json, logging
from flask import Flask, render_template, request
import spotpp


app = Flask(__name__)

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)
    
def defineTerm():
   q = input("Please enter a search term: \n")
   return q
   
def callApi(q):
   params = {'q': q}
   paramstr = urllib.parse.urlencode(params)
   baseurl = 'https://www.googleapis.com/books/v1/volumes'
   sunrequest = baseurl + '?' + paramstr
   try:
      sunrequeststr = urllib.request.urlopen(sunrequest)
   except urllib.error.HTTPError as e:
      print("Error trying to retrieve data: " + str(e))
      return None
   except urllib.error.URLError as e:
      if hasattr(e,"code"):
         print("The server couldn't fulfill the request.")
         print("Error code: ", e.code)
      elif hasattr(e,'reason'):
         print("We failed to reach a server")
         print("Reason: ", e.reason)
      else:
         print("got", response.geturl())
      return None
   sunrequeststrs = sunrequeststr.read()
   sundata = json.loads(sunrequeststrs)
   #print(pretty(sundata))
   return sundata


def extract_keywords(sundata):
   import yake
   kw_extractor = yake.KeywordExtractor()
   for item in sundata['items'][0:1]:
      if 'searchInfo' in item.keys():
         text = '"""' + item['searchInfo']['textSnippet'] + '"""'
         language = "en"
         max_ngram_size = 2
         deduplication_threshold = 0.9
         numOfKeywords = 10
         custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=numOfKeywords, features=None)
         keywords = custom_kw_extractor.extract_keywords(text)
         list = []
         for kw in keywords:
            list.append(kw[0])
   return list



def keywordstrip(keywords):
    list = []
    for item in keywords:
        item = item.replace(" ", "%20")
        list.append(item)
    print(list)
    return list

if __name__ == "__main__":
    # Used when running locally only.
	# When deploying to Google AppEngine, a webserver process
	# will serve your app.
    app.run(host="localhost", port=8000, debug=True)
