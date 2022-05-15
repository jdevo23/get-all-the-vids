import os
from typing import List
import json
import re
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from keys import bearer_token as TWITTER_BEARER_TOKEN

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube"]
CLIENT_SECRETS_FILE = os.getcwd() + "\\google_client_secret.json"
TEST_CREDENTIALS = os.getcwd() + "\\credentials.json"


class CustomError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __str__(self):
        return f"{self.status_code} error: {self.message}"


class EmptyValueError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"Error: {self.message}"


def get_video_links_from_tweet(tweet_id: str) -> List:
    """
        Queries Twitter API for any links in replies to the selected tweet.
        Twitter API doesn't allow filtering for just YouTube links, so non-YT links will
        need filtering out later.
    """
    headers = {
        'Authorization': 'Bearer ' + TWITTER_BEARER_TOKEN,
    }
    url = f"https://api.twitter.com/2/tweets/search/recent?query=conversation_id:{tweet_id}&tweet.fields=entities&max_results=100"

    arr = []

    try:
        _r = requests.get(url, headers=headers)
        json_r = _r.json()

        if _r.ok:
            data = json_r["data"]
            for _x in data:
                if "entities" in _x and "urls" in _x["entities"]:
                    for _y in _x["entities"]["urls"]:
                        arr.append(_y["expanded_url"])
        else:
            raise CustomError(status_code=_r.status_code,
                              message="Invalid Request. Unable to access Twitter API.")
    except Exception as _e:
        raise _e

    return arr


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """ refreshes the access token required for accessing Google OAuth 2.0 APIs """
    url = "https://oauth2.googleapis.com/token"
    params = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }

    access_token = ""

    try:
        _r = requests.post(url, data=params)
        json_r = _r.json()
        if _r.ok:
            response = json_r
            access_token = response["access_token"]
        else:
            raise CustomError(status_code=_r.status_code,
                              message="Invalid Request. Unable to refresh access token.")
    except Exception as _e:
        raise _e

    return access_token


def get_authenticated_service() -> str:
    """ Service for getting a valid access token, required to access YouTube APIs """
    access_token = ""

    try:
        # User attempts login with refresh token
        f = open(CLIENT_SECRETS_FILE)
        data = json.load(f)["installed"]

        if "refresh_token" in data:
            access_token = refresh_access_token(
                data["client_id"], data["client_secret"], data["refresh_token"])
        else:
            raise KeyError(
                'KeyError: "refresh_token" key missing in JSON. User must log in via browser to gain a valid refresh token.')
    except KeyError as _e:
        # This block runs when user is first using the app. The refresh token returned here lets the user sign in without going through the full flow
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)

        credentials = flow.run_local_server()
        access_token = credentials.token

        obj = {
            "installed": {
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "project_id": "get-all-the-vids",
                "rapt_token": credentials.rapt_token,
                "redirect_uris": ["http://localhost"],
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "token": credentials.token
            }
        }

        with open(CLIENT_SECRETS_FILE, 'w+') as outfile:
            json.dump(obj, outfile)

    return access_token


def create_playlist(access_token: str, title: str, description: str) -> str:
    """ Create a YouTube playlist """
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    params = {
        "snippet": {
            "title": title,
            "description": description
        }
    }

    playlist_id = ""

    try:
        _r = requests.post(
            "https://www.googleapis.com/youtube/v3/playlists?part=snippet", data=json.dumps(params), headers=headers)
        json_r = _r.json()
        if _r.ok:
            playlist_id = json_r["id"]
        else:
            raise CustomError(status_code=_r.status_code,
                              message="Invalid Request. Unable to create playlist.")
    except Exception as _e:
        raise _e

    return playlist_id


def extract_video_id(video_id: str) -> str:
    """ Finds an ID in a URL, if that URL is a YouTube link """
    regex = r".*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*"
    matches = re.findall(regex, video_id)

    if matches:
        return matches[0]
    return ""


def insert_playlist_item(access_token: str, video_id: str, playlist_id: str) -> bool:
    """ Inserts a video into a playlist """
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    params = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }

    return_val = False

    _r = requests.post("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet",
                       data=json.dumps(params), headers=headers)
    if _r.ok:
        return_val = True

    return return_val


def get_tweet_id() -> str:
    """ Retrieve the ID from a Twitter URL """
    _input = input("Enter a tweet URL or ID: ")
    _id = re.findall(r"(?:twitter.com/\w+/status/)?(\d+)", _input)

    if _id:
        return _id[0]
    else:
        return ""


def get_user_input(input_type: str) -> str:
    """ User inputs that are used as parameters for creating a playlist """
    ref = {
        "title": {
            "string": "Enter a title for the playlist: ",
            "char_limit": 150
        },
        "description": {
            "string": "Enter a description for the playlist (optional): ",
            "char_limit": 5000
        },
    }

    while True:
        _input = input(ref[input_type]["string"])

        if input_type == "title" and len(_input) == 0:
            print("Title is required.")
        elif len(_input) > ref[input_type]["char_limit"]:
            char_limit = ref[input_type]["char_limit"]
            print(f"{input_type} must be within {char_limit} characters.")
        else:
            return _input


def parse_video_links(links: List) -> List:
    """ inputs a list of video URLs and returns a list of IDs """
    video_links = [extract_video_id(link) for link in links]
    video_ids = list(filter(lambda x: x, video_links))

    if not video_ids:
        raise EmptyValueError(
            "Could not find any YouTube links in replies.")

    return video_ids


def main() -> None:
    """ main app flow """
    try:
        tweet_id = get_tweet_id()
        video_links = get_video_links_from_tweet(tweet_id)
        video_ids = parse_video_links(video_links)

        title = get_user_input("title")
        description = get_user_input("description")

        access_token = get_authenticated_service()
        playlist_id = create_playlist(access_token, title, description)
        count = 0

        for video_id in video_ids:
            if video_id:
                insert_successful = insert_playlist_item(
                    access_token, video_id, playlist_id)
                if insert_successful:
                    count += 1

        print(f'Successfully inserted {count} videos into playlist "{title}"')
        return None
    except CustomError as _e:
        print(_e)
        return None
    except EmptyValueError as _e:
        print(_e)
        return None
    except Exception as _e:
        print("Unknown error: ", _e)
        return None


if __name__ == "__main__":
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    main()
