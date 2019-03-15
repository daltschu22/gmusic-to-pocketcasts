#!/usr/bin/env python

import os
import sys
import configparser
from gmusicapi import Mobileclient
import pocketcasts
import pprint
import json

pp = pprint.PrettyPrinter(indent=4)

class GmusicApi:

    def __init__(self, account):
        self.account = account
        # self.open_config()
        self.api = Mobileclient()
        self.oauth_credential = str('{}/oauth.cred'.format(os.getcwd()))
        self.connect_to_api()

        # Attributes
        self.podcasts = {}

    def connect_to_api(self):
        if os.path.isfile(self.oauth_credential):
            print("\nExisting oauth file found! Using that to login...\n")
            self.oauth_login()
        else:
            print("\nNOTE: You must authenticate to the google music api, follow the directions.")
            print("The oauth credential file will be stored in this script directory as oauth.cred\n")
            self.perform_oauth()
            self.oauth_login()

    def oauth_login(self):
        try:
            self.api.oauth_login(
                oauth_credentials=self.oauth_credential,
                device_id=self.api.FROM_MAC_ADDRESS
            )
        except Exception as e:
            print("\nGoogle Music API login failed: {}".format(e))
            quit()

    def perform_oauth(self):
        try:
            # self.api.login(self.email, self.password, self.api.FROM_MAC_ADDRESS)
            self.api.perform_oauth(storage_filepath=self.oauth_credential)
        except Exception as e:
            print("\nGoogle Music API login failed: {}".format(e))
            quit()

class PocketCastsApi:

    def __init__(self, account):
        self.account = account
        self.open_config()
        self.__api = pocketcasts
        self.login()

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
            self.api = self.__api.Api(self.email, self.password)
            # self.api = self.__api.Pocketcasts.login(username=self.email, password=self.password)
        except Exception as e:
            print("Pocket Casts API login failed: {}".format(e))
            quit()

def millis_to_minutes(millis):
    """Return minutes from input of milliseconds."""
    minutes = round((int(millis)/(1000*60))%60, 2)
    return minutes

def main():

    # Create API objects
    gmusic = GmusicApi('gmusic')
    # pcasts = PocketCastsApi('pocketcasts')

    # Get all podcasts and episodes from google music
    gmusic_podcasts = gmusic.api.get_all_podcast_series()
    gmusic_podcast_episodes = gmusic.api.get_all_podcast_episodes()

    # Assemble the podcasts into a dicionary with each key being the name of the podcast
    for gmusic_pod in gmusic_podcasts:
        title_of_pod = gmusic_pod['title']
        gmusic.podcasts[title_of_pod] = gmusic_pod

    # All all the episodes to a list under the correct dictionary
    for episode in gmusic_podcast_episodes:
        try:
            series_title = episode['seriesTitle']
        except Exception:
            print("Couldnt get series title for {}".format(episode))
        if series_title in gmusic.podcasts:
            if 'episodes' in gmusic.podcasts[series_title]:
                gmusic.podcasts[series_title]['episodes'].append(episode)
            else:
                gmusic.podcasts[series_title]['episodes'] = [episode]


    for podcast_name, value in gmusic.podcasts.items():
        for ep in value['episodes']:
            if 'playbackPositionMillis' in ep:
                min_location = millis_to_minutes(ep['playbackPositionMillis'])
                print("You are currently listening to {} at {} minutes".format(ep['title'], min_location))



    # for cast in pcasts:
    #     if 'playbackPositionMillis' in cast:

    #         pp.pprint(cast)
      
    # pocketcasts_my_podcasts = pcasts.api.my_podcasts()

    # pocket_pod_names = []
    # for pod in pocketcasts_my_podcasts:
    #     pocket_pod_names.append(pod.title)

    # gmusic_pod_names = []
    # for pod in gmusic_podcast_list:
    #     gmusic_pod_names.append(pod['title'])
    #     if pod not in pocket_pod_names:
    #         print("{} - Is not subsribed on PocketCasts. -> Adding".format(pod['title']))



if __name__ == "__main__":
    main()
