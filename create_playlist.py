"""
Step 1: Log into Youtube
Step 2: Grab our liked Videos
Step 3: Create a New Playlist
Step 4: Search for the Song
Step 5: Add this song into the new Spotify playlist
"""
import json
import requests
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import youtube_dl

from requests.exceptions import HTTPError
from secrets import access_token, username


class CreatePlaylist:

    def __init__(self):
        self.user_id = username
        self.token = access_token
        self.youtube_client = self.get_youtube_client()
        self.all_sing_info = {}

    # Step 1: Log into Youtube
    def get_youtube_client(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)
        return youtube_client

    # Step 2: Grab our liked Videos & Creating a Dictionary of important Song Information
    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute()

        # collect each video and get important information
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

            # use you tube_dl to collect the song name and artist name
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            # save the important info
            self.all_sing_info[video_title] = {
                "youtube_url": youtube_url,
                "song_name": song_name,
                "artist": artist,
                # add the songs uri
                "spotify_uri": self.get_spotify_uri(song_name, artist)
            }

    # Step 3: Create a New Playlist
    def create_playlist(self):
        request_body = json.dumps({
            "name": "Banger",
            "description": "All Liked Youtube Videos",
            "public": True
        })
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.token)
            }
        )
        response_json = response.json()
        # playlist_id
        return response_json["id"]
        # Step 4: Search for the Song

    def get_spotify_uri(self, song_name, artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.token)
            }

        )
        response_json = response.json()
        # Getting the item from the URI
        songs = response_json["tracks"]["items"]
        uri = songs[0]["uri"]
        return uri

    # Step 5: Add this song into the new Spotify playlist
    def add_song_to_playlist(self):
        # populate our songs dictionary
        self.get_liked_videos()
        # collect all of uri
        uris = []
        for song, info in self.all_sing_info.items():
            uris.append(info["spotify_uri"])
        # create a new playlist
        playlist_id = self.create_playlist()
        # add all songs into new playlist
        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
        try:
            response = requests.post(
                query,
                data=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {}".format(self.token)
                }
            )
            response.raise_for_status()
        except HTTPError as http_err:
            return (f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            return (f'Other error occurred: {err}')  # Python 3.6
        else:
            response_json = response.json()
            return response_json


if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()
