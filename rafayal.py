from dotenv import load_dotenv
import logging, verboselogs, os
from time import sleep
import schedule
import threading

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

is_finals = []
his = []
transcription_processed = False

class Raf:
    @staticmethod
    def stt():
        try:
            deepgram = DeepgramClient(DG_API_KEY)
            dg_connection = deepgram.listen.live.v("1")

            def on_open(self, open, **kwargs):
                print(f"Deepgram Connection Open")

            def on_message(self, result, **kwargs):
                global is_finals, his, transcription_processed
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

                        # Process the first transcription in a separate thread
                        threading.Thread(target=Raf.ai, args=(his,)).start()

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

            options = LiveOptions(
                model="nova-2",
                punctuate=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                endpointing=True
            )

            addons = {
                "no_delay": "true"
            }

            print("\n\nPress Enter to stop recording...\n\n")
            if not dg_connection.start(options, addons=addons):
                print("Failed to connect to Deepgram")
                return

            global microphone
            microphone = Microphone(dg_connection.send)
            microphone.start()

            input("\n")
            microphone.finish()
            dg_connection.finish()
            print("Finished")
            return his

        except Exception as e:
            print(f"Could not open socket: {e}")
            return []

    @staticmethod
    def ai(his):
        prompt = '\n\n'.join(his)
        print(prompt)
        try:
            res = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": """
                            You are an advanced AI chatbot (Name : Raffayal) who generates responses like a person. You will be getting the query 
                            by text format which is a transcription of a live audio. So expect some filler words from the query.
                        """},
                    {"role": "user", "content": f"""
                            Generate a response for the following query with in 60 words, if requiered you can use 300 words.: \n{prompt}
                        """}
                ],
                model="llama3-8b-8192",
                temperature=0.5
            )
            print("\n", res.choices[0].message.content)
            return res.choices[0].message.content

        except Exception as e:
            print(f"Error during summarization: {e}")
            return ""

if __name__ == "__main__":
    stt_thread = threading.Thread(target=Raf.stt)
    stt_thread.start()
    stt_thread.join()