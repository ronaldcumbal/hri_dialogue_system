import os

DATA_PATH = os.path.join("/home/roncu858/Github/hri_dialogue_system", "data")

def synchronize_data():
    for participant in os.listdir(DATA_PATH):
        if participant.startswith('p'):
            print(f"Processing participant: {participant}")
            for data in os.listdir(os.path.join(DATA_PATH, participant)):
                if data.endswith(".log"):
                    log_path = os.path.join(DATA_PATH, participant, data)
            
    log_data = process_log_file(log_path)

def process_log_file(log_path):
    with open(log_path, 'r') as file:
        log_data = file.readlines()

    interruptions_list = []
    conditions_list = []
    for i, line in enumerate(log_data):
        if "Publishing: START" in line:
            start_timestamp = line.split("[wizard_interface-1]")[0].strip()

        elif "Publishing: INTERRUPTION" in line:
            timestamp = line.split("[wizard_interface-1]")[0].strip()
            interruptions_list.append(timestamp)

        elif "Publishing: LOADING " in line:
            condition = line.split("Publishing: LOADING ")[-1].strip()
            timestamp = line.split("[wizard_interface-1]")[0].strip()
            conditions_list.append((condition, timestamp))

    print(f"Interruption responses at: \n")
    for interruption in interruptions_list:
        print(f"{float(interruption) - float(start_timestamp)}")

    print(f"\nConditions:\n")
    for condition, timestamp in conditions_list:
        print(f"{condition}: {float(timestamp) - float(start_timestamp)}")


if __name__ == "__main__":
    synchronize_data()