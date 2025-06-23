from gtts import gTTS
from mutagen.mp3 import MP3
import os
import json
import time
import numpy as np

REPO_PATH = "/home/roncu858/Github/hri_dialogue_system"
AUDIOFILE_PATH = os.path.join(REPO_PATH, "scripts", 'audiofile.mp3')
UTTERANCES_FILE =  os.path.join(REPO_PATH, "ros2_workspace", "src", "woz_reception", "config", 'utterances.json')
OUTPUT_FILE = os.path.join(REPO_PATH, "ros2_workspace", "src", "woz_reception", "config", 'utterance_duration.json')


def read_utterances():
    with open(UTTERANCES_FILE, 'r') as file:
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
    tts.save(AUDIOFILE_PATH)

def compute_duration(utterances):
    data = {}
    sec_per_word = []
    for utt in utterances:
        generate_audio(utt)
        # Assuming the audio file is saved as 'audiofile.mp3'
        audio = MP3(AUDIOFILE_PATH)
        time.sleep(1)
        duration = audio.info.length
        data[utt] =  duration
        sec_per_word.append(duration/len(utt.split()))
        print("Utterance: ", utt, " Tokens: ", len(utt.split()), " Duration: ", duration)

    with open(OUTPUT_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    print("Average: ", np.mean(sec_per_word))

if __name__ == "__main__":
    utts = read_utterances()
    compute_duration(utts)
