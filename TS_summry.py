from dotenv import load_dotenv
import logging, verboselogs, os
from time import sleep, time
import schedule
import threading

import tweepy
from groq import Groq
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

load_dotenv()
DG_API_KEY = "7d3771a441578cd8380a7eb3c393975684145e76"
client = Groq(api_key=os.environ["GROQ_API_KEY"])

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET_KEY = os.getenv("TWITTER_API_KEY_SECREAT")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECREAT")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Authenticate
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

tweet_client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET_KEY,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

is_finals = []
running = True
last_checked_index = 0
#last_transcription_time = time()

class TS_bot:
    @staticmethod
    def stt():
        global his
        his = []

        try:
            deepgram: DeepgramClient = DeepgramClient(DG_API_KEY)
            dg_connection = deepgram.listen.live.v("1")

            def on_open(self, open, **kwargs):
                print(f"Deepgram Connection Open")

            def on_message(self, result, **kwargs):
                global is_finals
                sentence = result.channel.alternatives[0].transcript

                if len(sentence) == 0:
                    return
                if result.is_final:
                    is_finals.append(sentence)
                    if result.speech_final:
                        utterance = ' '.join(is_finals)
                        print(f'speaker: """{utterance}"""')
                        is_finals = []
                        his.append(utterance)
                        #last_transcription_time = time()

            def on_metadata(self, metadata, **kwargs):
                pass

            def on_speech_started(self, speech_started, **kwargs):
                pass

            def on_utterance_end(self, utterance_end, **kwargs):
                global is_finals
                if len(is_finals) > 0:
                    utterance = ' '.join(is_finals)
                    print(f"Deepgram Utterance End: {utterance}")
                    is_finals = []

            def on_close(self, close, **kwargs):
                print(f"Deepgram Connection Closed")

            def on_error(self, error, **kwargs):
                print(f"Deepgram Handled Error: {error}")

            def on_unhandled(self, unhandled, **kwargs):
                print(f"Deepgram Unhandled Websocket Message: {unhandled}")

            dg_connection.on(LiveTranscriptionEvents.Open, on_open)
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
            dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
            dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
            dg_connection.on(LiveTranscriptionEvents.Close, on_close)
            dg_connection.on(LiveTranscriptionEvents.Error, on_error)
            dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

            options: LiveOptions = LiveOptions(
                model="nova-2",
                punctuate=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                endpointing=True
            )

            addons = {
                # Prevent waiting for additional numbers
                "no_delay": "true"
            }

            print("\n\nPress Enter to stop recording...\n\n")
            if dg_connection.start(options, addons=addons) is False:
                print("Failed to connect to Deepgram")
                return

            # Open a microphone stream on the default input device
            microphone = Microphone(dg_connection.send)
            microphone.start()

            while running:
                sleep(0.1)

            microphone.finish()
            dg_connection.finish()
            print("Finished")
            return his

        except Exception as e:
            print(f"Could not open socket: {e}")
            return
        
    @staticmethod
    def summery(histo):
        prompt = '\n\n'.join(histo)
        try:
            res = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Summarize the following conversation within 40 words, highlighting the main points and any important information discussed."}
                ],
                model="llama3-8b-8192",
                temperature=0.5,
                max_tokens=49
            )
            print("\n", res.choices[0].message.content)
            return res.choices[0].message.content
        except Exception as e:
            print(f"Error during summarization: {e}")
            return ""
    
    @staticmethod
    def check_importance(hiss):
        y = "important"
        n = "not important"

        prompt = '\n\n'.join(hiss)
        try:
            res = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an AI that determines the importance of conversations."},
                    {"role": "user", "content": f"""
                        Check if the given conversation has important information. If it has then respond with '{y}', 
                        and if it does not carry any important info then respond with '{n}': \n\n{prompt}
                        """
                    }
                ],
                model="gemma-7b-it"
            )
            response = res.choices[0].message.content.strip()
            print("\n ========= ", response, " ========= \n")
            return response
        except Exception as e:
            print(f"Error during importance check: {e}")
            return "not important"

    @staticmethod
    def tweet_post(sum):
        try:
            tweet_summ = f"@Swapnil_110401 : {sum}"
            res = tweet_client.create_tweet(text=tweet_summ)
            print("Tweeted successfully")
            print(f"https://twitter.com/user/status/{res.data['id']}")
            print("\n")
        except Exception as e:
            print(f"Error while tweeting: {e}")
            print("\n")

    @staticmethod
    def summer_and_tweet():
        global his, last_checked_index
        if his:
            # Check only new parts of the conversation since the last check
            new_his = his[last_checked_index:]
            if new_his:
                ans = TS_bot.check_importance(new_his)
                if ans == "important":
                    sum = TS_bot.summery(his)  # Summarize from the beginning
                    if sum:
                        TS_bot.tweet_post(sum)
                # Update the last checked index
                last_checked_index = len(his)

schedule.every(1).minutes.do(TS_bot.summer_and_tweet)

def stop_program():
    global running
    running = False
    print("Stopping program...")

# def check_inactivity():
#     global last_transcription_time, running
#     while running:
#         sleep(10)
#         if time() - last_transcription_time > 10:
#             TS_bot.summer_and_tweet()
#             stop_program()

if __name__ == "__main__":
    def run_stt():
        TS_bot.stt()

    # Start the STT in a separate thread
    stt_thread = threading.Thread(target=run_stt)
    stt_thread.start()

    # Start the inactivity checker in a separate thread
    # inactivity_thread = threading.Thread(target=check_inactivity)
    # inactivity_thread.start()

    try:
        while running:
            schedule.run_pending()
            sleep(1)
    except KeyboardInterrupt:
        stop_program()

    stt_thread.join()
    #inactivity_thread.join()
    print("Program stopped.")
