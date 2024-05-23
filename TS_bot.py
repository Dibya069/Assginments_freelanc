import tweepy
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET_KEY = os.getenv("TWITTER_API_KEY_SECREAT")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECREAT")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Authenticate
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

client = tweepy.Client(bearer_token=BEARER_TOKEN,
                    consumer_key=API_KEY,
                    consumer_secret=API_SECRET_KEY,
                    access_token=ACCESS_TOKEN,
                    access_token_secret=ACCESS_TOKEN_SECRET)

#Verifying the credential
try:
    user = client.get_me()
    print(f"Authentication OK, logged in as {user.data.username}")
except Exception as e:
    print(f"Error during authentication: {e}")


# Function to create a tweet
def tweet_post():
    tweet = """
        Young minds seeking wisdom's gentle breeze,
        On agony's meaning, let me take you to the trees,
        Of human experience, where emotions ebb and flow,
        Where pain and anguish stir, and the heart dothknow.

        #agony #philoshophy #AI_poem #GenAI
    """
    try:
        res = client.create_tweet(text = tweet)
        print("Tweeted successfully")
        print(f"https://twitter.com/user/status/{res.data['id']}")
    except Exception as e:
        print(f"Error while tweeting: {e}")

# Function to respond to mentions
def respond_to_mentions():
    mentions = api.mentions_timeline(count=5)
    for mention in mentions:
        print(f"Found mention from @{mention.user.screen_name} - {mention.text}")
        try:
            api.update_status(f"@{mention.user.screen_name} Thanks for the mention!", mention.id)
            print(f"Replied to @{mention.user.screen_name}")
        except Exception as e:
            print(f"Error while replying: {e}")

# Main function
if __name__ == "__main__":
    tweet_post()
    #respond_to_mentions()