

import urllib.request, urllib.error, urllib.parse, json, logging
from flask import Flask, render_template, request, session, redirect, url_for, logging
from flask_bootstrap import Bootstrap
import getkeywords

app = Flask(__name__)
Bootstrap(app)

from pants import CLIENT_ID, CLIENT_SECRET


GRANT_TYPE = 'authorization_code'

# This is a code we'll use to crypotgraphically secure our sessions
# I set it to CLIENT_SECRET for simplicity here.
app.secret_key = CLIENT_SECRET
def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

### Helper functions ####

### This adds a header with the user's access_token to Spotify requests
def spotifyurlfetch(url, access_token, params=None):
    headers = {'Authorization': 'Bearer ' + access_token}
    req = urllib.request.Request(
        url=url,
        data=params,
        headers=headers
    )
    response = urllib.request.urlopen(req)
    return response.read()


### Handlers ###

### this will handle our home page
#@app.route("/")
def index(q):
    if 'user_id' in session:
        url = "https://api.spotify.com/v1/search?type=playlist&q=" + q
        # in the future, should make this more robust so it checks
        # if the access_token is still valid and retrieves a new one
        # using refresh_token if not
        response = json.loads(spotifyurlfetch(url, session['access_token']))
        #print(pretty(response))
        playlists = response['playlists']['items']
    else:
        playlists = None
    return playlists


### this handler will handle our authorization requests
@app.route("/auth/login")
def login_handler():
    # after  login; redirected here
    # did we get a successful login back?
    args = {}
    args['client_id'] = CLIENT_ID

    verification_code = request.args.get("code")
    if verification_code:
        # if so, we will use code to get the access_token from Spotify
        # This corresponds to STEP 4 in https://developer.spotify.com/web-api/authorization-guide/

        args["client_secret"] = CLIENT_SECRET
        args["grant_type"] = GRANT_TYPE
        # store the code we got back from Spotify
        args["code"] = verification_code
        # the current page
        args['redirect_uri'] = request.base_url
        data = urllib.parse.urlencode(args).encode("utf-8")

        # We need to make a POST request, according to the documentation
        # headers = {'content-type': 'application/x-www-form-urlencoded'}
        url = "https://accounts.spotify.com/api/token"
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, data=data)
        response_dict = json.loads(response.read())
        access_token = response_dict["access_token"]
        refresh_token = response_dict["refresh_token"]

        # Download the user profile. Save profile and access_token
        # in Datastore; we'll need the access_token later

        ## the user profile is at https://api.spotify.com/v1/me
        profile = json.loads(spotifyurlfetch('https://api.spotify.com/v1/me',
                                             access_token))

        ## Put user info in session
        ## it is not generally a good idea to put all of this in
        ## session, because there is a risk of sensitive info
        ## (like access token) being exposed.
        session['user_id'] = profile["id"]
        session['displayname'] = profile["display_name"]
        session['access_token'] = access_token
        session['profile_url'] = profile["external_urls"]["spotify"]
        session['api_url'] = profile["href"]
        session['refresh_token'] = refresh_token
        return redirect(url_for('main_handler'))
    else:
        # not logged in yet-- send the user to Spotify to do that
        # This corresponds to STEP 1 in https://developer.spotify.com/web-api/authorization-guide/
        args['redirect_uri'] = request.base_url
        args['response_type'] = "code"
        # ask for the necessary permissions -
        # see details at https://developer.spotify.com/web-api/using-scopes/
        args[
            'scope'] = "user-library-modify playlist-modify-private playlist-modify-public playlist-read-collaborative playlist-read-private"

        url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(args)
        print(redirect(url))
        return redirect(url)


## this handler logs the user out by making the cookie expire
@app.route("/auth/logout/")
def logout_handler():
    ## remove each key from the session!
    for key in list(session.keys()):
        session.pop(key)
    return redirect(url_for('main_handler'))


@app.route("/",methods=["GET","POST"])
def main_handler():
    app.logger.info("In MainHandler")
    if request.method == 'POST':
        app.logger.info(request.form.get('book'))
    name = request.form.get('username')
    book = request.form.get('book')
    #print(playlists)
    if book:
        #if form filled in, greet them using this data
        bookdata = getkeywords.callApi(book)
        if bookdata is not None:
            title = bookdata['items'][0]['volumeInfo']['title']
            keywords = getkeywords.extract_keywords(bookdata)
            keywords = getkeywords.keywordstrip(keywords)
            playlist = index(keywords[0])
            heylist = index(keywords[3])
            if 'imageLinks' in bookdata['items'][0]['volumeInfo']:
                imageLinks = bookdata['items'][0]['volumeInfo']['imageLinks']['thumbnail']
            else:
                imageLinks = None
            if len(playlist):
                playlistname = playlist[0]['name']
                playlist = playlist[0]['external_urls']['spotify']
                print(playlistname)
            else:
                playlist = None
                playlistname = None
            if len(heylist):
                heylistname = heylist[0]['name']
                heylist = heylist[0]['external_urls']['spotify']
            else:
                heylist = None
                heylistname = None
                return render_template('index.html',
                page_title=title,
                bookdata=bookdata, keywords = keywords, imageLinks = imageLinks, playlist = playlist, user = session, playlistname = playlistname
                )
            return render_template('index.html',
                page_title=title,
                bookdata=bookdata, keywords = keywords, imageLinks = imageLinks, playlist = playlist, user = session, heylist = heylist, playlistname = playlistname, heylistname = heylistname
                )
        else:
            return render_template('index.html',
                page_title=" Form - Error",
                prompt="Something went wrong with the API Call")
    elif book=="":
        return render_template('index.html',
            page_title="Form - Error",
            prompt="We need a book")
    else:
        return render_template('index.html',page_title="Book Form")

