#!/usr/bin/env python

import os
import sys
import configparser
from gmusicapi import Mobileclient
import pprint as pprint
import pickle
from collections import Counter
import requests
import json

pp = pprint.PrettyPrinter(indent=4)

class gmusicConfig:

    def __init__(self, account):
        self.account = account
        self.open_config()
        self.api = Mobileclient()

    def open_config(self):
        config = configparser.ConfigParser()

        cf = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "api.cfg"
            )
        if not config.read([cf]):
            print("No login configuration file found!")

        self.email = config.get(self.account, 'email')
        self.password = config.get(self.account, 'password') 

    def login(self):
        try:
            logged_in = self.api.login(self.email, self.password, self.api.FROM_MAC_ADDRESS)
            if logged_in == False:
                print("Google Music API login failed")
                sys.exit()
            if logged_in == True:
                return logged_in
        except:
            print("Google Music API login failed")

class songKickConfig:

    def __init__(self, account):
        self.account = account
        self.open_config()

    def open_config(self):
        config = configparser.ConfigParser()

        cf = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "api.cfg"
            )
        if not config.read([cf]):
            print("No login configuration file found!")

        self.api_key = config.get(self.account, 'api_key')


def count_list(song_list):
    play_count_list = []

    for song in song_list:
        if 'playCount' in song:
            song_artist = song['artist']
            song_count = song['playCount']
            dict = {'artist': song_artist, 'count': song_count}
            play_count_list.append(dict)

    #Combine values of list
    top_list = Counter()
    for play_count in play_count_list:
        top_list[play_count['artist']] += play_count['count']

    return top_list

def get_top_artists(all_artists, top_count):
    top_artists = dict(Counter(all_artists).most_common(top_count))

    return top_artists

def get_songkick_artist_id(top_artists, songkick):
    songkick_search_url = 'http://api.songkick.com/api/3.0/search/artists.json'

    artist_ids = []

    for artist in top_artists:
        # pp.pprint(artist)
        if '&' in artist:
            artist = artist.replace("&", "and")

        parameters = {"apikey": songkick.api_key, "query": artist, 'page': 1}
        try:
            r = requests.get(songkick_search_url, params=parameters)
            # print(r.json()['resultsPage']['results']['artist'][0])
        except Exception as e:
            print("Artist lookup failed!")
            print(e)
        try:
            artist_ids.append(r.json()['resultsPage']['results']['artist'][0]['id'])
        except KeyError as e:
            print('KeyError: No artist returned!')
            # print(e)

    return artist_ids


def main():
    top_count = 50

    gmusic = gmusicConfig('gmusic')
    gmusic.login()  #Login to the API

    #Grab top songs from gmusic and output to pickle file
    # pickle_out = open("songs.pickle","wb")
    # song_list = gmusic.api.get_all_songs()
    # pickle.dump(song_list, pickle_out)

    #Input pickle file of gmusic data
    pickle_in = open('songs.pickle','rb')
    song_list = pickle.load(pickle_in)
    
    all_artists = count_list(song_list)    #Get top artists
    top_artists = get_top_artists(all_artists, top_count)   #Get top n artists
    
    #Create songkick object
    songkick = songKickConfig('songkick')

    #Get artist id's from songkick API
    artist_ids = get_songkick_artist_id(top_artists, songkick)

    for artist_id in artist_ids:
        print(artist_id)
        url = 'http://api.songkick.com/api/3.0/artists/{artist_id}/calendar.json'
        parameters = {"apikey": songkick.api_key, "artist_id": artist_id}# "artist_id": 3184796}
        r = requests.get(url, params=parameters)
        pp.pprint(r.json()['resultsPage']['results'])

    # pp.pprint(vars(r))

    # pp.pprint(artist_ids)

    # for artist in top_artists:
    #     pp.pprint(type(artist))


    # print(top_artist)



if __name__ == "__main__":
    main()
