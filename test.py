import json
import queue
import threading
import time
import wave
from pathlib import Path
import os
from datetime import datetime

import pyaudio
import sounddevice as sd
import soundfile as sf
import openai

client = openai
openai.api_key = "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"
# %%
# Mapping from condition to analysis
condition_analysis = {
    "Below": "Your sales are less than even the minimum level - You have immense possibilities",
    "Equal min (5-10% Variance)": "Your sales are just at the minimum level - You have immense possibilities",
    "Above & below Avg.": "Your sales are less than average - You should do much better",
    "Equal avg (5-10% Variance)": "Your sales are average - There is great scope for you",
    "Above & below Best": "Your sales are better than average - There is scope to do still better",
    "Equal max (5-10% Variance)": "Your sales are among the best - Congratulations! You may still want to better it",
    "Above": "You are among the top performers - You could guide others from the community"
}
data = [
    {"City": "Tier1", "Area": "High Street", "Sales Per Sq. Ft.": 2500, "Parameter": "Min", "Condition": "Below"},
    {"City": "Tier1", "Area": "High Street", "Sales Per Sq. Ft.": 2500, "Parameter": "Minimum",
     "Condition": "Equal min (5-10% Variance)"},
    {"City": "Tier1", "Area": "High Street", "Sales Per Sq. Ft.": 2500, "Parameter": "Min",
     "Condition": "Above & below Avg."},
    {"City": "Tier1", "Area": "High Street", "Sales Per Sq. Ft.": 3500, "Parameter": "Average",
     "Condition": "Equal avg (5-10% Variance)"},
    {"City": "Tier1", "Area": "High Street", "Sales Per Sq. Ft.": 3500, "Parameter": "Avg",
     "Condition": "Above & below Best"},
    {"City": "Tier1", "Area": "High Street", "Sales Per Sq. Ft.": 5000, "Parameter": "Best",
     "Condition": "Equal max (5-10% Variance)"},
    {"City": "Tier1", "Area": "High Street", "Sales Per Sq. Ft.": 5000, "Parameter": "Max", "Condition": "Above"},
    {"City": "Tier1", "Area": "Residential", "Sales Per Sq. Ft.": 2000, "Parameter": "Min", "Condition": "Below"},
    {"City": "Tier1", "Area": "Residential", "Sales Per Sq. Ft.": 2000, "Parameter": "Minimum",
     "Condition": "Equal min (5-10% Variance)"},
    {"City": "Tier1", "Area": "Residential", "Sales Per Sq. Ft.": 2000, "Parameter": "Min",
     "Condition": "Above & below Avg."},
    {"City": "Tier1", "Area": "Residential", "Sales Per Sq. Ft.": 3000, "Parameter": "Average",
     "Condition": "Equal avg (5-10% Variance)"},
    {"City": "Tier1", "Area": "Residential", "Sales Per Sq. Ft.": 3000, "Parameter": "Avg",
     "Condition": "Above & below Best"},
    {"City": "Tier1", "Area": "Residential", "Sales Per Sq. Ft.": 4000, "Parameter": "Best",
     "Condition": "Equal max (5-10% Variance)"},
    {"City": "Tier1", "Area": "Residential", "Sales Per Sq. Ft.": 4000, "Parameter": "Max", "Condition": "Above"},
    {"City": "Tier1", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Min", "Condition": "Below"},
    {"City": "Tier1", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Minimum",
     "Condition": "Equal min (5-10% Variance)"},
    {"City": "Tier1", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Min",
     "Condition": "Above & below Avg."},
    {"City": "Tier1", "Area": "Low rent area", "Sales Per Sq. Ft.": 2500, "Parameter": "Average",
     "Condition": "Equal avg (5-10% Variance)"},
    {"City": "Tier1", "Area": "Low rent area", "Sales Per Sq. Ft.": 2500, "Parameter": "Avg",
     "Condition": "Above & below Best"},
    {"City": "Tier1", "Area": "Low rent area", "Sales Per Sq. Ft.": 3500, "Parameter": "Best",
     "Condition": "Equal max (5-10% Variance)"},
    {"City": "Tier1", "Area": "Low rent area", "Sales Per Sq. Ft.": 3500, "Parameter": "Max", "Condition": "Above"},
    {"City": "Tier2", "Area": "High Street", "Sales Per Sq. Ft.": 2500, "Parameter": "Min", "Condition": "Below"},
    {"City": "Tier2", "Area": "High Street", "Sales Per Sq. Ft.": 2500, "Parameter": "Minimum",
     "Condition": "Equal min (5-10% Variance)"},
    {"City": "Tier2", "Area": "High Street", "Sales Per Sq. Ft.": 2500, "Parameter": "Min",
     "Condition": "Above & below Avg."},
    {"City": "Tier2", "Area": "High Street", "Sales Per Sq. Ft.": 3000, "Parameter": "Average",
     "Condition": "Equal avg (5-10% Variance)"},
    {"City": "Tier2", "Area": "High Street", "Sales Per Sq. Ft.": 3000, "Parameter": "Avg",
     "Condition": "Above & below Best"},
    {"City": "Tier2", "Area": "High Street", "Sales Per Sq. Ft.": 3500, "Parameter": "Best",
     "Condition": "Equal max (5-10% Variance)"},
    {"City": "Tier2", "Area": "High Street", "Sales Per Sq. Ft.": 3500, "Parameter": "Max", "Condition": "Above"},
    {"City": "Tier2", "Area": "Residential", "Sales Per Sq. Ft.": 2000, "Parameter": "Min", "Condition": "Below"},
    {"City": "Tier2", "Area": "Residential", "Sales Per Sq. Ft.": 2000, "Parameter": "Minimum",
     "Condition": "Equal min (5-10% Variance)"},
    {"City": "Tier2", "Area": "Residential", "Sales Per Sq. Ft.": 2000, "Parameter": "Min",
     "Condition": "Above & below Avg."},
    {"City": "Tier2", "Area": "Residential", "Sales Per Sq. Ft.": 2500, "Parameter": "Average",
     "Condition": "Equal avg (5-10% Variance)"},
    {"City": "Tier2", "Area": "Residential", "Sales Per Sq. Ft.": 2500, "Parameter": "Avg",
     "Condition": "Above & below Best"},
    {"City": "Tier2", "Area": "Residential", "Sales Per Sq. Ft.": 3000, "Parameter": "Best",
     "Condition": "Equal max (5-10% Variance)"},
    {"City": "Tier2", "Area": "Residential", "Sales Per Sq. Ft.": 3000, "Parameter": "Max", "Condition": "Above"},
    {"City": "Tier2", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Min", "Condition": "Below"},
    {"City": "Tier2", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Minimum",
     "Condition": "Equal min (5-10% Variance)"},
    {"City": "Tier2", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Min",
     "Condition": "Above & below Avg."},
    {"City": "Tier2", "Area": "Low rent area", "Sales Per Sq. Ft.": 2000, "Parameter": "Average",
     "Condition": "Equal avg (5-10% Variance)"},
    {"City": "Tier2", "Area": "Low rent area", "Sales Per Sq. Ft.": 2000, "Parameter": "Avg",
     "Condition": "Above & below Best"},
    {"City": "Tier2", "Area": "Low rent area", "Sales Per Sq. Ft.": 2500, "Parameter": "Best",
     "Condition": "Equal max (5-10% Variance)"},
    {"City": "Tier2", "Area": "Low rent area", "Sales Per Sq. Ft.": 2500, "Parameter": "Max", "Condition": "Above"},
    {"City": "Tier3", "Area": "High Street", "Sales Per Sq. Ft.": 2000, "Parameter": "Min", "Condition": "Below"},
    {"City": "Tier3", "Area": "High Street", "Sales Per Sq. Ft.": 2000, "Parameter": "Minimum",
     "Condition": "Equal min (5-10% Variance)"},
    {"City": "Tier3", "Area": "High Street", "Sales Per Sq. Ft.": 2000, "Parameter": "Min",
     "Condition": "Above & below Avg."},
    {"City": "Tier3", "Area": "High Street", "Sales Per Sq. Ft.": 2500, "Parameter": "Average",
     "Condition": "Equal avg (5-10% Variance)"},
    {"City": "Tier3", "Area": "High Street", "Sales Per Sq. Ft.": 2500, "Parameter": "Avg",
     "Condition": "Above & below Best"},
    {"City": "Tier3", "Area": "High Street", "Sales Per Sq. Ft.": 3000, "Parameter": "Best",
     "Condition": "Equal max (5-10% Variance)"},
    {"City": "Tier3", "Area": "High Street", "Sales Per Sq. Ft.": 3000, "Parameter": "Max", "Condition": "Above"},
    {"City": "Tier3", "Area": "Residential", "Sales Per Sq. Ft.": 1500, "Parameter": "Min", "Condition": "Below"},
    {"City": "Tier3", "Area": "Residential", "Sales Per Sq. Ft.": 1500, "Parameter": "Minimum",
     "Condition": "Equal min (5-10% Variance)"},
    {"City": "Tier3", "Area": "Residential", "Sales Per Sq. Ft.": 1500, "Parameter": "Min",
     "Condition": "Above & below Avg."},
    {"City": "Tier3", "Area": "Residential", "Sales Per Sq. Ft.": 2000, "Parameter": "Average",
     "Condition": "Equal avg (5-10% Variance)"},
    {"City": "Tier3", "Area": "Residential", "Sales Per Sq. Ft.": 2000, "Parameter": "Avg",
     "Condition": "Above & below Best"},
    {"City": "Tier3", "Area": "Residential", "Sales Per Sq. Ft.": 2500, "Parameter": "Best",
     "Condition": "Equal max (5-10% Variance)"},
    {"City": "Tier3", "Area": "Residential", "Sales Per Sq. Ft.": 2500, "Parameter": "Max", "Condition": "Above"},
    {"City": "Tier3", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Min", "Condition": "Below"},
    {"City": "Tier3", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Minimum",
     "Condition": "Equal min (5-10% Variance)"},
    {"City": "Tier3", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Min",
     "Condition": "Above & below Avg."},
    {"City": "Tier3", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Average",
     "Condition": "Equal avg (5-10% Variance)"},
    {"City": "Tier3", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Avg",
     "Condition": "Above & below Best"},
    {"City": "Tier3", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Best",
     "Condition": "Equal max (5-10% Variance)"},
    {"City": "Tier3", "Area": "Low rent area", "Sales Per Sq. Ft.": 1500, "Parameter": "Max", "Condition": "Above"}
]


def classify_sales(city, area, monthly_sales, store_size):
    # Calculate sales per square foot
    sales_per_sq_ft = monthly_sales / store_size

    # Initialize variables to store the minimum, average, and best sales per sq ft for the given city and area
    min_sales = float('inf')
    avg_sales = 0
    best_sales = 0

    # Find the minimum, average, and best sales per sq ft for the given city and area
    for record in data:
        if record["City"] == city and record["Area"] == area:
            if record["Parameter"] == "Minimum" and record["Sales Per Sq. Ft."] < min_sales:
                min_sales = record["Sales Per Sq. Ft."]
            elif record["Parameter"] == "Average":
                avg_sales = record["Sales Per Sq. Ft."]
            elif record["Parameter"] == "Best":
                best_sales = record["Sales Per Sq. Ft."]

    # Classify the sales per sq ft
    condition = ""
    if sales_per_sq_ft < min_sales * 0.9:
        condition = "Below"
    elif min_sales * 0.9 <= sales_per_sq_ft < min_sales * 1.1:  # Allowing 10% variance for 'min'
        condition = "Equal min (5-10% Variance)"
    elif min_sales * 1.1 <= sales_per_sq_ft < avg_sales * 0.9:
        condition = "Above & below Avg."
    elif avg_sales * 0.9 <= sales_per_sq_ft < avg_sales * 1.1:  # Allowing 10% variance for 'average'
        condition = "Equal avg (5-10% Variance)"
    elif avg_sales * 1.1 <= sales_per_sq_ft < best_sales * 0.9:
        condition = "Above & below Best"
    elif best_sales * 0.9 <= sales_per_sq_ft < best_sales * 1.1:  # Allowing 10% variance for 'max'
        condition = "Equal max (5-10% Variance)"
    elif sales_per_sq_ft >= best_sales * 1.1:
        condition = "Above"

    # Get the analysis for the classified condition
    analysis = condition_analysis.get(condition, "No matching record found")

    return analysis


def calculate_total_renovation_cost(store_size_sqft):
    # Costs per square foot for each head of expense (as an example)
    costs_per_sqft = {
        'Fixtures': 250,  # Racks, Bins, checkout fixtures, etc.
        'Fixtures_back_office': 30,  # Workstations, ladder, files, cabinets, lockers, etc.
        'Air_conditioning': 200,  # Cost for split AC per square foot
        'Equipment': 25,  # Scales, cash safe, insect killer, etc.
        'Electricals': 150,  # Lights, fixtures, fans, cabling, etc.
        'Chiller / Freezers': 160,
        'Security': 35,
        'IT Equipments': 250
    }
    fixed_cost = {
        'Signages': 100000
    }
    # Calculate total cost by summing the product of each cost per sqft and the store size
    total_cost = sum(cost * store_size_sqft for cost in costs_per_sqft.values()) + sum(fixed_cost.values())

    return total_cost


def add_new_user_to_json(file_path, username, thread_id):
    with open(file_path, 'r') as file:
        user_data = json.load(file)
    timestamp_started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_user = {
        'username': username,
        'thread': thread_id,
        'timestamp_started': timestamp_started,
        'timestamp_ended': ''  # Initially empty, to be updated when conversation ends
    }
    user_data.append(new_user)
    with open(file_path, 'w') as file:
        json.dump(user_data, file, indent=4)


def add_user_pincode(username, pincode, file_path='user.json'):
    """
    Adds or updates the pincode for a user in the user.json file.
    The user and thread ID are already existing in the JSON.

    :param file_path: Path to the user.json file.
    :param username: The username of the user.
    :param pincode: The pincode to be stored or updated.
    """
    print(pincode)
    user_found = False

    # Read the existing data from the file
    with open(file_path, 'r') as file:
        user_data = json.load(file)

    # Check for the user in the existing data
    for user in user_data:
        if user['username'] == username:
            user_found = True
            user['pincode'] = pincode  # Add or update the pincode
            break

    # If user is not found, indicate an error or handle accordingly
    if not user_found:
        print("User not found.")
        # Optionally, handle the case where the user is not in the file
        # For instance, you might want to add the user or raise an exception

    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(user_data, file, indent=4)

    return None


def record_audio(filename, stop_event, audio_queue):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording... Press return key to stop.")

    while not stop_event.is_set():
        data = stream.read(CHUNK)
        audio_queue.put(data)

    print("Finished recording")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(list(audio_queue.queue)))


# Transcribe audio
def transcribe_audio(filename):
    with open(filename, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        return transcript


def generate_audio(text):
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
         model="tts-1",
         voice="nova",
         input=text
    )
    response.stream_to_file(speech_file_path)
    audio_data, sample_rate = sf.read(speech_file_path)
    sd.play(audio_data, sample_rate)
    sd.wait()


theUser = "Kirana"
# theUserInput = "mera 400053 mein store size hai 200sq ft. my sales is 200000 per month. meri sales kaisi hai?"

audio_filename = "recorded_audio.wav"
stop_event = threading.Event()
audio_queue = queue.Queue()
#
record_thread = threading.Thread(target=record_audio, args=(audio_filename, stop_event, audio_queue))
record_thread.start()
#
input("Press the return key to stop recording...\n")
stop_event.set()
record_thread.join()
#
transcription = transcribe_audio(audio_filename)
print(transcription)

input_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Check if user exists and handle accordingly
user_found = False
with open('user.json', 'r') as file:
    user_data = json.load(file)

for i in user_data:
    if i['username'] == theUser:
        user_found = True
        if len(i['thread']) < 1:
            thread = client.beta.threads.create()
            i['thread'] = thread.id
            i['timestamp_started'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            i['timestamp_ended'] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")  # Initially empty, to be updated when conversation ends
            with open('user.json', 'w') as file:
                json.dump(user_data, file, indent=4)
        break

if not user_found:
    thread = client.beta.threads.create()
    add_new_user_to_json('user.json', theUser, thread.id)

# Reload user_data to get the active thread ID and timestamps
with open('user.json', 'r') as file:
    user_data = json.load(file)

activeUserThreadId = ""
for i in user_data:
    if i['username'] == theUser:
        activeUserThreadId = i['thread']

message = client.beta.threads.messages.create(
    thread_id=activeUserThreadId,
    role="user",
    content=transcription
)

run = client.beta.threads.runs.create(
    thread_id=activeUserThreadId,
    assistant_id="asst_W9WA6vCaOCwxCRO2byOg6EgW",

)

while True:
    time.sleep(2)
    run = client.beta.threads.runs.retrieve(
        thread_id=activeUserThreadId,
        run_id=run.id
    )
    print(run.status)
    if run.status == 'completed':
        break
    elif run.status == "requires_action":
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []

        for tool_call in tool_calls:
            print(tool_call.function.name)
            if tool_call.function.name == "store_renovation_cost_estimator":
                args = json.loads(tool_call.function.arguments)['store_size']
                result = calculate_total_renovation_cost(args)
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": result,
                    },
                )
            elif tool_call.function.name == "sales_potential_assessment":
                args = json.loads(tool_call.function.arguments)
                location = args['location']
                store_size = args['store_size']
                current_sales = args['current_sales']
                area_type = args['area_type']
                result = classify_sales(location, area_type, current_sales, store_size)
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": result,
                    },
                )
            elif tool_call.function.name == "store_user_pincode":
                args = json.loads(tool_call.function.arguments)
                pincode = args['pincode']
                add_user_pincode(theUser, pincode)
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": "Location stored successfully",
                    },
                )
            elif tool_call.function.name == "salt_circle_calculator":
                args = json.loads(tool_call.function.arguments)
                salt = args['salt_packets_sold']
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": salt,
                    },
                )
            # Add additional tool call handling here if needed

        if tool_outputs:
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=activeUserThreadId,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

    else:
        pass

messages = client.beta.threads.messages.list(
    thread_id=activeUserThreadId
)

response_message = messages.data[0].content[0].text.value

# Generate a unique filename
filename = os.path.join('chats', f"thread_{activeUserThreadId}.json")
# Get the current timestamp
response_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Write conversation to file
try:
    with open(filename, 'a') as file:  # 'a' to append to the file if it exists
        conversation_data = {
            'input timestamp': input_time,
            'user_input': transcription,
            'response timestamp': response_time,
            'ai_response': response_message
        }
        json.dump(conversation_data, file)
        file.write("\n")  # Adding a newline for separation between entries
except IOError as e:
    # Handle file writing errors here
    print(f"Error writing to file: {e}")

# First, read the data from the file
with open('user.json', 'r') as file:
    user_data = json.load(file)

# Update the timestamp_ended for the specific user
user_found = False
for i in user_data:
    if i['username'] == theUser:
        i['timestamp_ended'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_found = True
        break

# Then, write the updated data back to the file
if user_found:
    with open('user.json', 'w') as file:
        json.dump(user_data, file, indent=4)
else:
    print("User not found.")


print(f'{theUser} : {transcription}')
print(f'Assistant: {response_message}')
generate_audio(response_message)
