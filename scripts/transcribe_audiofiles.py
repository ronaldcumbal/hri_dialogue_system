import whisper
import os
import json
import pandas as pd

DATA_PATH = os.path.join("/home/roncu858/Github/hri_dialogue_system", "data")

MODEL = whisper.load_model("small")

def time_to_str(time_sec):
    minutes = int(float(time_sec)/60)
    seconds = (float(time_sec)/60 - float(time_sec)//60)*60
    time_str = f"{minutes}:{seconds:02.0f}"
    return time_str

def main():
    for participant in sorted(os.listdir(DATA_PATH)):
        if participant.startswith('p'):
            # if participant in ["p01", "p02", "p03", "p04", "p05", "p06", "p08", "p09", "p10", "p11"]:  # Exclude participants with incomplete data
            #     continue
            for audiofile in os.listdir(os.path.join(DATA_PATH, participant)):
                if audiofile.endswith(".mp3"):
                    print(f"Processing participant: {participant}")
                    audiofile_path = os.path.join(DATA_PATH, participant, audiofile)
                    transcribe_audiofile(audiofile_path, participant, audiofile)

def transcribe_audiofile(audio_path, participant, audiofile):

    textfile = audiofile.replace(".mp3", "_raw.txt")
    jsonfile = audiofile.replace(".mp3", "_raw.json")
    csvfile = audiofile.replace(".mp3", ".csv")

    result = MODEL.transcribe(audio_path)

    with open(os.path.join(DATA_PATH, participant, textfile), "w") as f:
        f.write(result["text"])

    with open(os.path.join(DATA_PATH, participant, jsonfile), "w") as f:
        json.dump(result, f, indent=4)

    data_list = []
    for segment in result["segments"]:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"].strip()
        data_list.append([participant, f"{start:.2f}", time_to_str(start), f"{end:.2f}", time_to_str(end), text])
    data_df = pd.DataFrame(data_list, columns=["participant","start_sec", "start_str", "end_sec", "end_str", "data"])
    data_df.to_csv(os.path.join(DATA_PATH, participant, csvfile), index=False)

if __name__ == "__main__":
    main()