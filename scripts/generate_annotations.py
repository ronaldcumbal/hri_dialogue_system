import os
import argparse
import pandas as pd

DATA_PATH = os.path.join("/home/roncu858/Github/hri_dialogue_system", "data")

def extract_image(video_path, time_sec, output_path):
    # pass
    command = f"ffmpeg -ss {time_sec} -i {video_path} -frames:v 1 {output_path}"
    os.system(command)

def main():
    data_df = pd.read_csv(os.path.join(DATA_PATH, "data_annotation.csv"))
    
    base_caption = "The person on the left is interacting with a robot. The person on the right needs to talk with the robot, but is currently waiting for their turn."
    attempt_caption = "The person on the left has finished interacting with a robot. The person on the right approaches to talk with the robot."
    approach_move_caption = "The person on the left is interacting with a robot. The person on the right appears to want to talk with the robot."
    approach_move_caption_rushed = "The person on the left is interacting with a robot. The person on the right appears to in a rush to talk with the robot."
    approach_talk_caption = "The person on the left is interacting with a robot. The person on the right approaches to talk with the robot."
    interruption_caption = "The person on the right is interacting with a robot. The person on the left waits while the other person asks a question."

    annotated_data = []
    for idx, row in data_df.iterrows():
        print(f"Processing row {idx+1}/{len(data_df)}")
        participant_id = row['participant']
        time_sec = float(row['time_sec'])
        time_str = row['time_str']
        event = row['event']

        video_front_path = os.path.join(DATA_PATH, participant_id, f"{participant_id}_front.mp4")
        video_furhat_path = os.path.join(DATA_PATH, participant_id, f"{participant_id}_furhat.mp4")
        image_id = f"{participant_id}_{str(time_sec).replace('.', '_')}"
        image_front_path = os.path.join(DATA_PATH, "front" ,f"{image_id}.png")
        image_furhat_path = os.path.join(DATA_PATH, "furhat" ,f"{image_id}.png")

        if event == "robot_speech":
            caption = base_caption
            time_sec = time_sec + 0.5
            image_id = f"{participant_id}_{str(time_sec).replace('.', '_')}"
            image_front_path = os.path.join(DATA_PATH, "front" ,f"{image_id}.png")
            image_furhat_path = os.path.join(DATA_PATH, "furhat" ,f"{image_id}.png")
            annotated_data.append([image_id, caption])
            extract_image(video_front_path, time_sec, image_front_path)
            extract_image(video_furhat_path, time_sec, image_furhat_path)

        elif event == "attempted_approach":
            caption = attempt_caption
            annotated_data.append([image_id, caption])
            extract_image(video_front_path, time_sec, image_front_path)
            extract_image(video_furhat_path, time_sec, image_furhat_path)

        elif event == "approach_move":
            if row['condition'] in ["rushed_condition", "very_rushed_condition"]:
                caption = approach_move_caption_rushed
            else:
                caption = approach_move_caption
            time_sec = time_sec + 0.10
            image_id = f"{participant_id}_{str(time_sec).replace('.', '_')}"
            image_front_path = os.path.join(DATA_PATH, "front" ,f"{image_id}.png")
            image_furhat_path = os.path.join(DATA_PATH, "furhat" ,f"{image_id}.png")
            annotated_data.append([image_id, caption])
            extract_image(video_front_path, time_sec, image_front_path)
            extract_image(video_furhat_path, time_sec, image_furhat_path)

        elif event == "approach_talk":
            caption = approach_talk_caption
            annotated_data.append([image_id, caption])
            extract_image(video_front_path, time_sec, image_front_path)
            extract_image(video_furhat_path, time_sec, image_furhat_path)

        elif event == "robot_speech_interruption":
            caption = interruption_caption
            annotated_data.append([image_id, caption])
            extract_image(video_front_path, time_sec, image_front_path)
            extract_image(video_furhat_path, time_sec, image_furhat_path)

        else:
            continue # Skip other events

    annotated_df = pd.DataFrame(annotated_data, columns=["image_id", "caption"])
    annotated_df.to_csv(os.path.join(DATA_PATH, "annotations.csv"), index=False)


if __name__ == "__main__":
    main()