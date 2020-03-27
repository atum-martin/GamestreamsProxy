
import requests
import random
import time
import json
import ssl
import urllib.parse
from http.server import BaseHTTPRequestHandler,HTTPServer

HOST_NAME = ''
PORT_NUMBER = 80

# @author Martin
# Date: 26/03/2020


def getContentForUrl(URL):
    r = requests.get(url=URL)
    obj = r.json()
    return obj

def getStreamsForChannel(channelName):
    URL = "https://api.twitch.tv/api/channels/"+channelName+"/access_token.json"

    headers = {
        'Client-ID': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
        'Accept': 'application/vnd.twitchtv.v3+json'
    }



    r = requests.get(url=URL, headers=headers)
    obj = r.json()
    print(str(obj["sig"]))
    print(str(obj["token"]))
    return parseM3U(streamUrls(obj["sig"], obj["token"], channelName))

def streamUrls(sig, token, channelName):
    URL = "https://usher.ttvnw.net/api/channel/hls/"+channelName+".m3u8"
    i = random.randint(1, 10000)
    params  = {
        'Accept': 'application/vnd.twitchtv.v3+json',
        'fast_bread': 'True',
        'player': 'twitchweb',
        'player': 'any',
        'allow_source': 'true',
        'allow_audio_only': 'true',
        'allow_spectre': 'false',
        'p': i,
        'schema': '_access_token_schema',
        'sig': sig,
        'token': token
    }



    r = requests.get(url=URL, params=params )
    print(str(r.content))
    return str(r.content)

def parseM3U(m3uContent):
    name=None
    resolution=None
    video=None

    data_set = [
    ]
    #trim some of the string encoding off and split
    for line in m3uContent[3:-1].split(","):
        if "NAME=" in line:
            name = line[6:-1]
        if "RESOLUTION=" in line:
            resolution = line[11:]
        if "VIDEO=" in line:
            video = line.split("\\n")[1]
            print(name+" "+resolution+ " "+video)
            streamEntry = {
                'quality': name,
                'resolution': resolution,
                'url': video,
                'activeStream': video
            }
            data_set.append(streamEntry)

    return data_set

class TwitchHttpHander(BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        #s.send_header("Content-type", "text/html")
        s.send_header("Access-Control-Allow-Origin", "*")
        s.end_headers()
    def do_GET(s):
        if s.path == "/":
            title(s)
            return
        if s.path == "/games/top":
            gamesTop(s)
            return
        if s.path == "/initial/streams":
            topStreams(s)
            return
        if s.path == "/mature-content":
            matureGames(s)
            return
        if "/streamers/" in s.path:
            gameName = s.path[11:]
            getStreamersForGame(s, gameName)
            return

        if "/stream/" in s.path:
            channelName = s.path[8:]
            print("channelName: "+channelName)
            streamsForChannel(s, channelName)
            return

        print("unknown: "+s.path)

def writeJson(s, data_set):
    print(data_set)
    s.send_response(200)
    s.send_header("Content-type", "json")
    s.send_header("Access-Control-Allow-Origin", "*")
    #s.send_header("Content-type", "text/plain")
    s.end_headers()
    #s.send_response_only(200, str(data_set).encode())
    s.wfile.write(json.dumps(data_set).encode())

def title(s):
    data_set = {"config": {"url": "http://192.168.0.99:820" }}
    writeJson(s, data_set)

def gamesTop(s):
    #data_set = {"top": [{"game": {"name": "csgo", "box": {"medium": "https://web.poecdn.com/gen/image/WzAsMSx7ImlkIjo1NTgsInNpemUiOiJhdmF0YXIifV0/75e7b71751/Path_of_Exile_Gallery_Image.jpg"}}}] }
    url = 'https://api.twitch.tv/kraken/games/top?client_id=jzkbprff40iqj646a697cyrvl0zt2m6&limit=30&offset=0'
    data_set = getContentForUrl(url)

    writeJson(s, data_set)

def getStreamersForGame(s, gameName):
    #data_set = {"streams": [{"channel": {"display_name": "shroud", "name": "shroud"},"preview": {"medium": "https://web.poecdn.com/gen/image/WzAsMSx7ImlkIjo1NTgsInNpemUiOiJhdmF0YXIifV0/75e7b71751/Path_of_Exile_Gallery_Image.jpg"}}] }
    #data_set = getStreamsForChannel("esl_csgo")

    url = 'https://api.twitch.tv/kraken/streams?client_id=jzkbprff40iqj646a697cyrvl0zt2m6&limit=30&game='+gameName
    data_set = getContentForUrl(url)
    writeJson(s, data_set)

def streamsForChannel(s, channelName):
    #url = 'http://192.168.0.99:820/proxy?path='+twitchurl
    data_set = getStreamsForChannel(channelName)
    writeJson(s, data_set)


def matureGames(s):
    data_set = {"mature_games": [ {"game": {"name": "csgo"}} ] }
    writeJson(s, data_set)

def topStreams(s):
    #data_set = {"streams": [ {"channel": {"name": "shroud"}} ] }
    #this is the initial stream thats loaded in the app
    url = 'https://api.twitch.tv/kraken/streams?client_id=jzkbprff40iqj646a697cyrvl0zt2m6&limit=30'
    data_set = getContentForUrl(url)
    writeJson(s, data_set)


def startWebServer():
    server_class = HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), TwitchHttpHander)
    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        #httpd.socket = ssl.wrap_socket(httpd.socket,keyfile="localhost.pem",certfile='localhost.pem', server_side=True)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))

#channelName = "esl_csgo"
#getStreamsForChannel(channelName)

startWebServer()


