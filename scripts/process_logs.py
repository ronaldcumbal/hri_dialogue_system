import os
import argparse
import pandas as pd

DATA_PATH = os.path.join("/home/roncu858/Github/hri_dialogue_system", "data")

def timestamp_to_time(timestamp):
    minutes = int(float(timestamp)/60)
    seconds = (float(timestamp)/60 - float(timestamp)//60)*60
    time_str = f"{minutes}:{seconds:02.0f}"
    return time_str

def process_log_file(log_path, participant_id=None):
    with open(log_path, 'r') as file:
        log_data = file.readlines()

    time_offset = {"p01": 1750764955.6129935 - 0.70, 
                   "p02": 1750768627.4287786 - 0.0, 
                   "p03": 1750770335.4142826 - 0.50,
                   "p04": 1750773971.5190411 - 0.20,
                   "p05": 1750775589.5603540 - 5.0,
                   "p06": 1750927656.8758488 - 0.25,
                   "p08": 1750930504.1742003 - 4.25,
                   "p09": 1750931897.8167529 - 5.70,
                   "p10": 1750945098.3173332 - 4.50,
                   "p11": 1750946865.7484255 - 6.00,
                   }

    data_list = []
    # conditions_list = []
    for i, line in enumerate(log_data):
        if "Publishing: START" in line:
            start_timestamp = line.split("[wizard_interface-1]")[0].strip()
            # print(f"Start timestamp: {start_timestamp}")

        elif "Publishing: INTERRUPTION" in line:
            timestamp = line.split("[wizard_interface-1]")[0].strip()
            timestamp = float(timestamp) - time_offset.get(participant_id, 0)
            time_sec = "{:.2f}".format(timestamp)
            time_str = timestamp_to_time(timestamp)
            data_list.append([participant_id, time_sec, time_str, condition, "interruption", ""])

        elif "Publishing: LOADING " in line:
            condition = line.split("Publishing: LOADING ")[-1].strip()
            timestamp = line.split("[wizard_interface-1]")[0].strip()
            timestamp = float(timestamp) - time_offset.get(participant_id, 0)
            time_sec = "{:.2f}".format(timestamp)
            time_str = timestamp_to_time(timestamp)
            data_list.append([participant_id, time_sec, time_str, condition, "new_condition", ""])

        elif "Publishing: speak " in line:
            utterance = line.split("Publishing: speak")[-1].strip()
            timestamp = line.split("[furhat_bridge-2]")[0].strip()
            timestamp = float(timestamp) - time_offset.get(participant_id, 0)
            time_sec = "{:.2f}".format(timestamp)
            time_str = timestamp_to_time(timestamp)
            data_list.append([participant_id, time_sec, time_str, condition, "robot_speech", utterance])
    return data_list

def time_to_timestamp(time_str, start_timestamp=0):
    minutes, seconds = map(int, time_str.split(':'))
    total_seconds = minutes * 60 + seconds
    timestamp = start_timestamp + total_seconds
    return timestamp


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description="Process log files and extract data.")
    argparser.add_argument('--time_str', type=str, default="0:00")
    args = argparser.parse_args()

    processed_data = []
    for participant in sorted(os.listdir(DATA_PATH)):
        if participant.startswith('p'):
            # if participant in ["p01", "p02", "p03", "p04", "p05", "p06", "p08", "p09", "p10", "p11"]:  # Exclude participants with incomplete data
            #     continue
            for data in os.listdir(os.path.join(DATA_PATH, participant, "raw")):
                if data.endswith(".log"):
                    print(f"Processing participant: {participant}")
                    log_path = os.path.join(DATA_PATH, participant, "raw", data)
                    logged_data = process_log_file(log_path, participant)
                    processed_data.extend(logged_data)
    
    participant_df = pd.DataFrame(processed_data, columns=["participant","time_sec", "time_str", "condition", "event", "data"])
    participant_df.to_csv(os.path.join(DATA_PATH, "data_processed.csv"), index=False)

    time_str = time_to_timestamp(args.time_str)
    print(time_str)