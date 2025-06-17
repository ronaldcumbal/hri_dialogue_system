from gtts import gTTS
from mutagen.mp3 import MP3
import json
import time
import numpy as np

def read_utterances():
    utterances_file = 'utterances.json'
    with open(utterances_file, 'r') as file:
        raw_utterances = json.load(file)

    utterances = []
    for key in raw_utterances:
        if key == "bridge":
            for utt in raw_utterances[key]:
                utt = parse_utterances(utt)
                utterances.extend(utt)
        else:
            for item in raw_utterances[key]:
                for utt in raw_utterances[key][item]:
                    utt = parse_utterances(utt)
                    utterances.extend(utt)

    utterances = list(set(utterances))  # Remove duplicates
    utterances.sort()  # Sort utterances alphabetically
    return utterances

def parse_utterances(utterance):
    data = []
    if "/" in utterance: 
        pased_data = utterance.split("/")
        for item in pased_data:
            if item.strip() != "":
                data.append(item.strip())
    else:
        data.append(utterance.strip())
    return data


def generate_audio(utt):
    tts = gTTS(utt, lang='en')
    tts.save('audiofile.mp3')

def compute_duration(utterances):
    data = {}
    sec_per_word = []
    for utt in utterances:
        generate_audio(utt)
        # Assuming the audio file is saved as 'audiofile.mp3'
        audio = MP3("audiofile.mp3")
        time.sleep(1)
        duration = audio.info.length
        data[utt] =  duration
        sec_per_word.append(duration/len(utt.split()))
        print("Utterance: ", utt, " Tokens: ", len(utt.split()), " Duration: ", duration)

    with open('utterance_duration.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)

    print("Average: ", np.mean(sec_per_word))

if __name__ == "__main__":
    utts = read_utterances()
    compute_duration(utts)
