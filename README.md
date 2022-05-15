# Get all the vids

## About

This is a command line program that allows you to scrape YouTube links from a comment thread on Twitter and use them to a generate a playlist.

At this moment in time, this script requires developer credentials from [Google OAuth 2.0](https://developers.google.com) and [Twitter](https://developer.twitter.com/en/apply-for-access).

### How to use

1. Obtain credentials from Twitter and Google
2. Clone the project using ```git clone https://github.com/jdevo23/get-all-the-vids [your_directory_name]```
3. Replace the ```TWITTER_BEARER_TOKEN``` and ```CLIENT_SECRETS_FILE``` with your own in the source code
4. Install packages using ```pip install -r requirements.txt```
5. Run script using ```python "C:/path/to/root"```
    1. Provide the link to a tweet. The Twitter API call will look for replies to that particular tweet.
    2. Enter remaining details
    

## Future improvements

* Allow anyone to use the program by porting it to a website and removing the need for developer credentials.
* The program currently can only fetch a maximum of 100 links from a thread. This could be increased by repeating the request. Twitter returns a "next" ID to allow for this.
* Allow user to select other details like the playlist thumbnail and privacy setting.