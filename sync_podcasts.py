#!/usr/bin/env python
"""Parse current podcasts in google music and add them to pocketcasts, including marking listened to episodes."""

import os
import configparser
from gmusicapi import Mobileclient
# import pocketcasts
# import requests
import pprint
import json
from requests_html import HTMLSession

pp = pprint.PrettyPrinter(indent=4)


class Gmusic:
    """Gmusic class for api operations."""

    def __init__(self, account):
        """Initialize class."""
        self.account = account
        self.api = Mobileclient()
        self._oauth_credential = str('{}/oauth.cred'.format(os.getcwd()))
        self.connect_to_api()

        # Attributes
        self.podcasts = {}

    def connect_to_api(self):
        """Connect to the gmusic api."""
        if os.path.isfile(self._oauth_credential):
            print("\nExisting oauth file found! Using that to login...\n")
            self.oauth_login()
        else:
            print("\nNOTE: You must authenticate to the google music api, follow the directions.")
            print("The oauth credential file will be stored in this script directory as oauth.cred\n")
            self.perform_oauth()
            self.oauth_login()

    def oauth_login(self):
        """Login using oath token."""
        try:
            self.api.oauth_login(
                oauth_credentials=self._oauth_credential,
                device_id=self.api.FROM_MAC_ADDRESS
            )
        except Exception as e:
            print("\nGoogle Music API login failed: {}".format(e))
            quit()

    def perform_oauth(self):
        """Request oath token from user."""
        try:
            self.api.perform_oauth(storage_filepath=self._oauth_credential)
        except Exception as e:
            print("\nGoogle Music API login failed: {}".format(e))
            quit()


class PocketCasts:
    """PocketCast class for api operations."""

    def __init__(self, account):
        """Initialize class."""
        self.account = account
        self.open_config()
        # self.__api = pocketcasts

        # self._session = requests.Session()

        self.login()


    def open_config(self):
        """Read the login info from the configuration file."""
        config = configparser.ConfigParser()

        cf = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "api.cfg"
            )
        if not config.read([cf]):
            print("No login configuration file found!")

        self.email = config.get(self.account, 'email')
        self.password = config.get(self.account, 'password')

    # def login(self):
    #     """Login to the api."""
    #     try:
    #         self.api = self.__api.Api(self.email, self.password)
    #         # self.api = self.__api.Pocketcasts.login(username=self.email, password=self.password)
    #     except Exception as e:
    #         print("Pocket Casts API login failed: {}".format(e))
    #         quit()

    def login(self):
        self._session = HTMLSession()

        login_json = {"email":self.email,"password":self.password,"scope":"webplayer"}
        response = self._session.post(
            "https://api.pocketcasts.com/user/login",
            headers={},
            json=login_json)
        response.raise_for_status()
        # TODO(Check if login was successful, code is 200 in every case)
    
        self._api_header = {"authorization": "Bearer " + str(response.json()['token'])}

    def get_my_podcasts(self):
        data = {"v": "1"}
        response = self._session.post(
            "https://api.pocketcasts.com/user/podcast/list",
            headers=self._api_header,
            json=data
            )
        response.raise_for_status()

        podcasts = []
        for podcast_json in response.json()['podcasts']:
            podcasts.append(podcast_json)

        self.podcasts = podcasts
        return podcasts

    def search_pod(self, search):
        params = {'term': search}
        response = self._session.post(
            "https://api.pocketcasts.com/discover/search",
            headers=self._api_header,
            data=params
            )
        response.raise_for_status()

        podcasts = []
        for podcast_json in response.json()['podcasts']:
            podcasts.append(podcast_json)

        return podcasts

def millis_to_minutes(millis):
    """Return minutes from input of milliseconds."""
    minutes = round((int(millis) / (1000*60)) % 60, 2)
    return minutes


def main():
    """Run program."""
    # Create API objects
    gmusic = Gmusic('gmusic')
    pcasts = PocketCasts('pocketcasts')

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
            print("Couldnt get series title for {}\n".format(episode))
            continue
        if series_title in gmusic.podcasts:
            if 'episodes' in gmusic.podcasts[series_title]:
                gmusic.podcasts[series_title]['episodes'].append(episode)
            else:
                gmusic.podcasts[series_title]['episodes'] = [episode]

    # Go through and find all the podcast episodes you have listened to
    for podcast in gmusic.podcasts.values():
        for ep in podcast['episodes']:
            if 'playbackPositionMillis' in ep:
                total_duration = int(ep['durationMillis'])
                playback_time = int(ep['playbackPositionMillis'])
                # Find the percentage of how much the user has listened to the episode
                percent_listened = int(round(100 * (playback_time/total_duration), 0))
                # print("You are currently listening to {} at {} percent".format(ep['title'], percent_listened))
                if percent_listened >= 90:
                    ep['listened'] = True
                else:
                    ep['listened'] = False
            else:
                ep['listened'] = False

    # for pod in gmusic.podcasts.values():
    #     for ep in pod['episodes']:
    #         if ep['listened']:
    #             print(ep['listened'], ep['title'], ep['seriesTitle'])

    # print(pcasts._api_header)

    # pcasts.my_podcasts()

    # print(pcasts.podcasts)
    # pcasts.login()

    # pp.pprint(pcasts.search_pod('Comedy Bang Bang: The Podcast'))


            # Use this to check author maybe?
            # if cast['author'] in response[0]['author']:
            #     print("MATCH 3! {} {}".format(cast['title'], response[0]['title']))

    for name, cast in gmusic.podcasts.items():
        response = pcasts.search_pod(cast['title'])
        if response[0]['title'] in cast['title']:
            print("MATCH 1! {} {}".format(cast['title'], response[0]['title']))
            continue
        elif len(response) > 2:
            for x in response:
                print("Trying to match {} with {}".format(cast['title'], x['title']))
                if cast['author'] in x['author']:
                    print("MATCH 2! {} {}".format(cast['title'], x['title']))
        else:
            print("No match for {}".format(name))
    

if __name__ == "__main__":
    main()
