from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import re
import yt_dlp as youtube_dl
from youtube_search import YoutubeSearch

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

print("!Spotify Playlist Downloader!\n")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

# Search for a playlist by link
def search_for_playlist_by_link(token, playlist_link):
    playlist_id = re.search(r"playlist\/([a-zA-Z0-9]+)", playlist_link).group(1)
    playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    all_tracks = []
    offset = 0
    limit = 100

    while True:
        headers = get_auth_header(token)
        params = {
            'limit': limit,
            'offset': offset
        }
        result = get(playlist_url, headers=headers, params=params)
        json_result = json.loads(result.content)

        if 'items' in json_result:
            all_tracks.extend(json_result['items'])
            offset += limit
            if offset >= json_result['total']:
                break
        else:
            print("Error: No 'items' in the API response.")
            break

    return all_tracks

token = get_token()
playlist_link = input("Paste The Spotify Playlist Link Here:")
download_directory = input("Where Do You Wanna Download This? ex: C:/Users/... :")
all_tracks_data = search_for_playlist_by_link(token, playlist_link)

if all_tracks_data:
    print(f"Playlist '{playlist_link}' has {len(all_tracks_data)} tracks:")
    for idx, track_info in enumerate(all_tracks_data):
        try:
            if track_info is not None and 'track' in track_info and 'name' in track_info['track']:

                track_name = track_info['track']['name']
                artist_name = track_info['track']['artists'][0]['name']  # Assuming there's only one artist
                print(f"{idx + 1}. {track_name} - {artist_name}")

                # Perform a YouTube search to get video results
                search_query = f"{track_name}-{artist_name} Full Audio-Version"
                search_result = YoutubeSearch(search_query, max_results=1).to_dict()
                # Create download directory if it doesn't exist
                if not os.path.exists(download_directory):
                    os.makedirs(download_directory)

                max_video_length_seconds = 450  #7 Minutes    
                video_id = search_result[0]['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_length = search_result[0]['duration']
                
                # Split video duration into parts
                duration_parts = video_length.split(':')
                
                if len(duration_parts) == 3:
                    hours, minutes, seconds = map(int, duration_parts)
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                elif len(duration_parts) == 2:
                    minutes, seconds = map(int, duration_parts)
                    total_seconds = minutes * 60 + seconds
                else:
                    total_seconds = int(duration_parts[0])

                if total_seconds >= max_video_length_seconds:
                    print(f"{track_name}-{artist_name}'s Video Length is longer than 7 Minutes")
                else:
                        # Full path for the MP3 file
                    mp3_filename = os.path.join(download_directory, f"{track_name}.mp3")

                        # Check if the MP3 file already exists
                    if not os.path.exists(mp3_filename):
                            # YouTubeDL options
                            ydl_opts = {
                                'format': 'bestaudio/best',
                                'postprocessors': [{
                                    'key': 'FFmpegExtractAudio',
                                    'preferredcodec': 'mp3',
                                    'preferredquality': '192',
                                }],
                                'outtmpl': os.path.join(download_directory, f"{track_name}"),
                                'postprocessor_args': [
                                '-metadata', f'artist={artist_name}',
                                '-metadata', f'title={track_name}',
                                ],
                            }

                            # Download the video using yt-dlp
                            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([video_url])
            else:
                print(f"{idx + 1}. Error: Invalid track information")
        except Exception as e:
            print(f"An error occurred while processing track {idx + 1}: {e}")



print("All Tracks Have Been Downloaded!")            