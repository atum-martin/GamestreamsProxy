
import requests
import random
import time
import json
import ssl
import urllib.parse
from urllib.parse import unquote
import threading
import os
from http.server import BaseHTTPRequestHandler,HTTPServer

HOST_NAME = '0.0.0.0'
if os.environ.get('PORT') is not None:
    PORT_NUMBER = int(os.environ['PORT'])
else :
    PORT_NUMBER = 820

class CacheVars:
    topGamesTwitchJson = None
    topGamesTwitchTimestamp = 0

    topStreamsTwitchJson = None
    topStreamsTwitchTimestamp = 0

    topStreamsForGameJson = dict()
    topStreamsForGameTimestamps = dict()

    loggingEnabled = False

# @author Martin
# Date: 26/03/2020

def log(msg):
    if(loggingEnabled):
        print(msg)


def getContentForUrl(URL):
    r = requests.get(url=URL)
    obj = r.json()
    return obj

def getTwitchJsonBrowserAPI(json):
    URL = 'https://gql.twitch.tv/gql'
    headers = {
        'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
        'Accept': '*/*',
        'X-Device-Id': '6b885390dcd3be57',
        'Referer': 'https://www.twitch.tv/directory',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    }

    r = requests.post(url=URL, headers=headers, data=json)
    obj = r.json()
    return obj

def getTopGamesTwitch():
    if time.time() - CacheVars.topGamesTwitchTimestamp < 60:
        return CacheVars.topGamesTwitchJson

    payload = topGamesJson()
    obj = getTwitchJsonBrowserAPI(payload)
    output = {"top": []}

    for game in obj[1]['data']['directoriesWithTags']['edges']:
        gameParsed = {"game": {"name": game['node']['displayName'], "box": {"medium": game['node']['avatarURL']}}}
        output['top'].append(gameParsed)
    CacheVars.topGamesTwitchJson = output
    CacheVars.topGamesTwitchTimestamp = time.time()
    log(output)
    return output

def getTopStreamsTwitch():
    if time.time() - CacheVars.topStreamsTwitchTimestamp < 60:
        return CacheVars.topStreamsTwitchJson

    payload = topStreamsJson()
    obj = getTwitchJsonBrowserAPI(payload)
    output = {"streams": []}

    for stream in obj[0]['data']['streams']['edges']:
        streamParsed = {"channel": {"display_name": stream['node']['broadcaster']['displayName'],"name": stream['node']['broadcaster']['login'],"box": {"medium": stream['node']['previewImageURL']}}, "preview": {"medium": stream['node']['previewImageURL']}}
        output['streams'].append(streamParsed)

    CacheVars.topStreamsTwitchJson = output
    CacheVars.topStreamsTwitchTimestamp = time.time()
    log(output)
    return output

def searchForChannelTwitch(searchTerm):
    searchTerm = unquote(searchTerm)

    log("getting streams for search: " + searchTerm + " ")
    payload = searchForTermJson(searchTerm)
    obj = getTwitchJsonBrowserAPI(payload)
    log(obj)
    output = {"streams": []}

    for stream in obj[0]['data']['searchFor']['channels']['items']:
        if stream['stream'] is None:
            continue
        log(stream)
        streamParsed = {"preview": {"medium": stream['stream']['previewImageURL']},
                        "channel": {"display_name": stream['displayName'],
                                    "name": stream['login']}}
        output['streams'].append(streamParsed)

    log(output)
    return output

def getTopStreamsForGame(gameName):
    gameName = unquote(gameName)
    if gameName in CacheVars.topStreamsForGameTimestamps and time.time() - CacheVars.topStreamsForGameTimestamps[gameName] < 60:
        return CacheVars.topStreamsForGameJson[gameName]


    log("getting streams for game: "+gameName+" ")
    payload = streamsForGameJson(gameName)
    obj = getTwitchJsonBrowserAPI(payload)
    log(obj)
    output = {"streams": []}

    for stream in obj[0]['data']['game']['streams']['edges']:
        streamParsed = {"preview": {"medium": stream['node']['previewImageURL']}, "channel": {"display_name": stream['node']['broadcaster']['displayName'],"name": stream['node']['broadcaster']['login']}}
        output['streams'].append(streamParsed)

    log(output)
    CacheVars.topStreamsForGameJson[gameName] = output
    CacheVars.topStreamsForGameTimestamps[gameName] = time.time()
    return output

def topStreamsJson():
    payload = '[{"operationName":"BrowsePage_Popular","variables":{"limit":30,"platformType":"all","options":{"sort":"RELEVANCE","tags":[],"recommendationsContext":{"platform":"web"},"requestID":"JIRA-VXP-2397"},"sortTypeIsRecency":false},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"3d1831781016217b1002b489682cd77f2726ff695b19f9704ffd8de35cd17edc"}}}]'
    return payload

def topGamesJson():
    payload = '[{"operationName":"Algolia_RequestInfo","variables":{},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"53a624acee2ecd22dd652c6c7beb352e30a62fc91260cf10d4a687cf08c881c0"}}},{"operationName":"BrowsePage_AllDirectories","variables":{"limit":30,"options":{"recommendationsContext":{"platform":"web"},"requestID":"JIRA-VXP-2397","sort":"RELEVANCE","tags":[]}},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"78957de9388098820e222c88ec14e85aaf6cf844adf44c8319c545c75fd63203"}}}]'
    return payload

def streamsForGameJson(gameName):
    getStreamsForGameJson = '[{"operationName":"DirectoryPage_Game","variables":{"name":"'+gameName.lower()+'","options":{"sort":"RELEVANCE","recommendationsContext":{"platform":"web"},"requestID":"JIRA-VXP-2397","tags":[]},"sortTypeIsRecency":false,"limit":30},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"f2ac02ded21558ad8b747a0b63c0bb02b0533b6df8080259be10d82af63d50b3"}}}]'
    return getStreamsForGameJson

def searchForTermJson(searchTerm):
    #json = '[{"operationName":"SearchTray_SearchSuggestions","variables":{"queryFragment":"'+searchTerm+'","requestID":"1441a3fb-b8cb-4cf4-bfec-9559427a28fd"},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"2a747ed872b1c3f56ed500d097096f0cf8d365d2d5131cbdc170ae502f9b406a"}}}]'
    json = '[{"operationName":"SearchResultsPage_SearchResults","variables":{"query":"'+searchTerm+'","options":{"targets":[{"index":"CHANNEL"}]}},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"aa914b7ce3bef314587273c1cef23d5ebf01b0815ec9e7b8b79ce28e7aa6e643"}}}]'
    return json

def getStreamsForChannel(channelName):
    URL = "https://api.twitch.tv/api/channels/"+channelName+"/access_token.json"

    headers = {
        'Client-ID': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
        'Accept': 'application/vnd.twitchtv.v3+json'
    }

    r = requests.get(url=URL, headers=headers)
    obj = r.json()
    log(str(obj["sig"]))
    log(str(obj["token"]))
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
    log(str(r.content))
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
            log(name+" "+resolution+ " "+video)
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
        log("get: " +s.path)
        if s.path == "/":
            title(s)
            return
        if s.path == "/games/top":
            gamesTop(s)
            return
        if s.path == "/enableDebug":
            CacheVars.loggingEnabled = True
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
            log("channelName: "+channelName)
            streamsForChannel(s, channelName)
            return
        if "/search-streams/" in s.path:
            searchTerm = s.path[16:]
            log("searchTerm: " + searchTerm)
            searchForChannel(s, searchTerm)
            return

        log("unknown: "+s.path)

def writeJson(s, data_set):
    log(data_set)
    s.send_response(200)
    s.send_header("Content-type", "json")
    s.send_header("Access-Control-Allow-Origin", "*")
    #s.send_header("Content-type", "text/plain")
    s.end_headers()
    #s.send_response_only(200, str(data_set).encode())
    s.wfile.write(json.dumps(data_set).encode())

def title(s):
    data_set = {"config": {"url": "https://atummartin-ttv.herokuapp.com/" }}
    writeJson(s, data_set)

def gamesTop(s):
    #data_set = {"top": [{"game": {"name": "csgo", "box": {"medium": "https://web.poecdn.com/gen/image/WzAsMSx7ImlkIjo1NTgsInNpemUiOiJhdmF0YXIifV0/75e7b71751/Path_of_Exile_Gallery_Image.jpg"}}}] }
    #url = 'https://api.twitch.tv/kraken/games/top?client_id=jzkbprff40iqj646a697cyrvl0zt2m6&limit=30&offset=0'
    #data_set = getContentForUrl(url)
    data_set = getTopGamesTwitch()
    writeJson(s, data_set)

def searchForChannel(s, searchTerm):
    #data_set = {"top": [{"game": {"name": "csgo", "box": {"medium": "https://web.poecdn.com/gen/image/WzAsMSx7ImlkIjo1NTgsInNpemUiOiJhdmF0YXIifV0/75e7b71751/Path_of_Exile_Gallery_Image.jpg"}}}] }
    #url = 'https://api.twitch.tv/kraken/games/top?client_id=jzkbprff40iqj646a697cyrvl0zt2m6&limit=30&offset=0'
    #data_set = getContentForUrl(url)
    data_set = searchForChannelTwitch(searchTerm)
    writeJson(s, data_set)

def getStreamersForGame(s, gameName):
    #data_set = {"streams": [{"channel": {"display_name": "shroud", "name": "shroud"},"preview": {"medium": "https://web.poecdn.com/gen/image/WzAsMSx7ImlkIjo1NTgsInNpemUiOiJhdmF0YXIifV0/75e7b71751/Path_of_Exile_Gallery_Image.jpg"}}] }
    #data_set = getStreamsForChannel("esl_csgo")

    #url = 'https://api.twitch.tv/kraken/streams?client_id=jzkbprff40iqj646a697cyrvl0zt2m6&limit=30&game='+gameName
    #data_set = getContentForUrl(url)
    data_set = getTopStreamsForGame(gameName)
    writeJson(s, data_set)

def topStreams(s):
    #data_set = {"streams": [ {"channel": {"name": "shroud"}} ] }
    #this is the initial stream thats loaded in the app
    #url = 'https://api.twitch.tv/kraken/streams?client_id=jzkbprff40iqj646a697cyrvl0zt2m6&limit=30'
    #data_set = getContentForUrl(url)
    data_set = getTopStreamsTwitch()
    writeJson(s, data_set)

def streamsForChannel(s, channelName):
    #url = 'http://192.168.0.99:820/proxy?path='+twitchurl
    data_set = getStreamsForChannel(channelName)

    writeJson(s, data_set)


def matureGames(s):
    data_set = {"mature_games": [ {"game": {"name": "csgo"}} ] }
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

#getTopStreamsForGame("Counter-strike: Global Offensive")

t = threading.Thread(target=startWebServer)
t.start()


#startWebServer()


