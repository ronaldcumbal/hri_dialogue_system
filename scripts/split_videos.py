import os
import subprocess

DATA_PATH = os.path.join("/home/roncu858/Github/hri_dialogue_system", "data")

def main():

    participant = "p01"
    participant_data = os.path.join(DATA_PATH, participant)
    output_video_path = os.path.join(participant_data, "clips")

    timestamps =[
        16.601218461990356,
        20.687004566192627,
        30.162201404571533,
        34.48036003112793,
        74.05115222930908,
        74.22431063652039,
        74.37787055969238,
        110.38374018669128,
        110.49437594413757,
        110.5815737247467,
        110.74325704574585
    ]

    for data in os.listdir(participant_data):
        if data.endswith(".mp3"):
            audio_path = os.path.join(DATA_PATH, participant, data)

        elif data.endswith(".avi"):
            furhat_video_path = os.path.join(DATA_PATH, participant, data)
            split_video(furhat_video_path, output_video_path, timestamps)


def split_video(furhat_video_path, output_video_path, timestamps):

    print(f"Processing participant: {output_video_path}")

    if not os.path.exists(output_video_path):
        os.makedirs(output_video_path)

    for i, time_start in enumerate(timestamps):
        time_end = time_start + 10
        video_output_path = f'{output_video_path}/{i}.avi'
        command = f"ffmpeg -i {furhat_video_path} -ss {time_start} -to {time_end} -c copy {video_output_path}"
        subprocess.call(command, shell=True)


def split_audio():
    pass

if __name__ == "__main__":
    main()