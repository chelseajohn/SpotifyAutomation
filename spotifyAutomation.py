'''
Work flow 
Step 1: Log into Youtube
Step 2: Take the liked videos
Step 3: Create a new playlist
Step 4: Search for a song
Step 5: Add the new song to new spotify playlist 
'''
import json
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl
import requests

from secrets import spotify_user_id, spotify_token

class CreatePlaylist:
    def _init_(self):
        self.user_id = spotify_user_id
        self.spotify_token= spotify_token
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    #Step 1: Log into Youtube
    def get_youtube_client(self):
        #copied from Youtube Data API
        #Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* Leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        #Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file,scopes)
        credentials = flow.run_console()

        #from Youtube DATA API
        youtube_client = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

        return youtube_client


     #Step 2: Take the liked videos and creating a dictionary of important song information
    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part ="snippet,contentDetails,statistics",
            myRating ="like"
        )
        response = request.execute()

        #collect each video and get important information
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url ="https://www.youtube.com/watch?v={}".format(item["id"])

            #use youtube_dl to collect the song name & artist name
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download = False)

            song_name = video["track"]
            artist = video["artist"]

            #save all this important info
            self.all_song_info[video_title] = {
                "youtube_url": youtube_url,
                "song_name": song_name,
                "artist": artist,

                #add the url, easy to get song to put into playlists
               "spotify_uri": self.get_spotify_uri(song_name,artist)
            }

    #Step 3: Create a new playlist
    def create_playlist(self):
        request_body= json.dumps({
                        "name": "Youtube Liked Vids",
                        "description": "Liked Youtube Videos",
                         "public": True
                                 })
                                 
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = requests.post(
            query,
            data = request_body,
            headers = {
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(spotify_token)
            }
            )
        response_json = response.json()

        #playlist id
        return response_json["id"]

    #Step 4: Search for a song
    def get_spotify_uri(self,song_name, artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                 "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        #only use the first song
        uri = songs[0]["uri"]
        return uri

    #Step 5: Add the new song to new spotify playlist 
    def add_song_to_playlist(self):
        #populate songs dictionary
        self.get_liked_videos()

        # collect all of url
        uris =[]
        for song,info in self.all_song_info.items():
            uris.append(info["spotify_uri"])

        # create a new playlist
        playlist_id = self.create_playlist()

        #add all songs into new playlist
        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data = request_data,
            headers={
                 "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(spotify_token)
        
            }
        )
        response_json = response.json()
        return response_json



if __name__ == '__main__':
    playlist = CreatePlaylist()
    playlist.add_song_to_playlist()