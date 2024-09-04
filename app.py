#import faiss
import json
import os
import time
from datetime import datetime
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from transformers import RagTokenizer, RagTokenForGeneration, RagRetriever

from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
#CORS(app, resources={r"/api/*": {"origins": "https://misraji.kiranafriends.com"}})
#CORS(app, resources={r"*": {"origins": "https://misraji.kiranafriends.com"}})
client = openai


# Initialize RAG components
# model_name = "facebook/rag-token-nq"
# retriever = RagRetriever.from_pretrained(model_name, index_name="exact", use_dummy_dataset=True)
# tokenizer = RagTokenizer.from_pretrained(model_name)
# rag_model = RagTokenForGeneration.from_pretrained(model_name, retriever=retriever)


#def enhance_response_with_rag(question):
#    inputs = tokenizer(question, return_tensors="pt")
#    with tokenizer.as_target_tokenizer():
#        labels = tokenizer(" ", return_tensors="pt").input_ids
#    outputs = rag_model.generate(input_ids=inputs['input_ids'], labels=labels.input_ids, num_beams=5)
#    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
#    return answer


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

def create_db_connection():
    try:
        connection = mysql.connector.connect(
                host='127.0.0.1',  # or your server IP
                database='MishrajiDatabase',
                user='KiranaUser',
                password='Kirana@123'
                )
        if connection.is_connected():
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
        return None


def sales_predictor(city, area, store_size):
    avg_sales = 0
    min_sales = 0
    print(city) 
    print(area)
    print(store_size)
    for record in data:
        if record["City"] == city and record["Area"] == area:
            if record["Parameter"] == "Minimum":
                min_sales = record["Sales Per Sq. Ft."]
            elif record["Parameter"] == "Average":
                avg_sales = record["Sales Per Sq. Ft."]
    average_sales = avg_sales*store_size
    print(average_sales)
    minimum_sales = min_sales*store_size
    print(minimum_sales)
    return (f"The average sales acording to the store size should be {average_sales} The minimum sales acording to the store size should be {minimum_sales}")


def calculate_total_renovation_cost(store_size_sqft):
    # Costs per square foot for each head of expense (as an example)
    costs_per_sqft = {
            'Fixtures': 275,  # Racks, Bins, checkout fixtures, etc.
            'Fixtures_back_office': 35,  # Workstations, ladder, files, cabinets, lockers, etc.
            'Air_conditioning': 225,  # Cost for split AC per square foot
            'Equipment': 30,  # Scales, cash safe, insect killer, etc.
            'Electricals': 175,  # Lights, fixtures, fans, cabling, etc.
            'Chiller / Freezers': 180,
            'Security': 45,
            'IT Equipments': 300
            }
    fixed_cost = {
            'Signages': 120000
            }
    # Calculate total cost by summing the product of each cost per sqft and the store size
    total_cost = sum(cost * store_size_sqft for cost in costs_per_sqft.values()) + sum(fixed_cost.values())

    return str(total_cost)


def add_new_user_to_json(file_path, thread_id,session_uuid):
    with open(file_path, 'r') as file:
        user_data = json.load(file)
    timestamp_started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_user = {
            'thread': thread_id,
            'timestamp_started': timestamp_started,
            'timestamp_ended': '',  # Initially empty, to be updated when conversation ends
            'session_uuid' : session_uuid
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

# def get_device_info():
#     user_agent = request.user_agent
#     device_info = {
#         'Browser': user_agent.browser,
#         'Platform': user_agent.platform,
#         'Version': user_agent.version,
#         'Language': user_agent.language,
#         'String': user_agent.string,
#     }
#     return device_info

def get_device_info():
    user_agent = request.user_agent
    device_ip = request.remote_addr  # Fetch the IP address
    device_info = {
            'IP': device_ip,
            'Browser': user_agent.browser,
            'Platform': user_agent.platform,
            'Version': user_agent.version,
            'Language': user_agent.language,
            'String': user_agent.string,
            }
    return device_info


def update_message_count(connection, kfid, thread_id):
    cursor = connection.cursor()
    # Check if the combination of KFId and ThreadID already exists in the table
    cursor.execute("SELECT MessageCount FROM ThreadMessageCounts WHERE KFId = %s AND ThreadID = %s", (kfid, thread_id))
    result = cursor.fetchone()
    if result:
        # If it exists, increment the count
        new_count = result[0] + 1
        cursor.execute("UPDATE ThreadMessageCounts SET MessageCount = %s WHERE KFId = %s AND ThreadID = %s", (new_count, kfid, thread_id))
    else:
        # If it does not exist, insert a new record with count as 1
        cursor.execute("INSERT INTO ThreadMessageCounts (KFId, ThreadID, MessageCount) VALUES (%s, %s, 1)", (kfid, thread_id))
    connection.commit()
    cursor.close()


def update_kfid_unique_thread_count(connection, kfid):
    cursor = connection.cursor()
    # Calculate the number of unique ThreadIDs for this KFId
    cursor.execute("SELECT COUNT(DISTINCT ThreadID) FROM ThreadMessageCounts WHERE KFId = %s", (kfid,))
    count_result = cursor.fetchone()[0]
    # Check if KFId already exists in the aggregate table
    cursor.execute("SELECT UniqueThreadCount FROM KFIdUniqueThreadCounts WHERE KFId = %s", (kfid,))
    result = cursor.fetchone()
    if result:
        # Update the count
        cursor.execute("UPDATE KFIdUniqueThreadCounts SET UniqueThreadCount = %s WHERE KFId = %s", (count_result, kfid))
    else:
        # Insert new entry
        cursor.execute("INSERT INTO KFIdUniqueThreadCounts (KFId, UniqueThreadCount) VALUES (%s, %s)", (kfid, count_result))
    connection.commit()
    cursor.close()

def get_next_kfid():
    connection = create_db_connection()
    if connection is None:
        return None

    cursor = connection.cursor()
    cursor.execute("SELECT KFId FROM LoginDetails ORDER BY ID DESC LIMIT 1")
    result = cursor.fetchone()

    if result:
        last_kfid = result[0]
        last_number = int(last_kfid[2:])
        next_number = last_number + 1
    else:
        next_number = 1

    next_kfid = f"MF{next_number:012d}"
    cursor.close()
    connection.close()

    return next_kfid


# Ensure you have the 'user.json' file in the same directory as this script
# with the appropriate structure.

@app.route('/')
def home():
    # Render the main chat interface
    return render_template('chat.html')


@app.route('/get_chat_messages', methods=['GET'])
def get_chat_messages():
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)  # Ensure we get column names in the result
            cursor.execute("SELECT * FROM ChatMessages")
            rows = cursor.fetchall()  # Fetch all results
            messages = []
            for row in rows:
                messages.append(row)
            cursor.close()
            return jsonify(messages), 200
        except Error as e:
            print("Error while fetching data from MySQL", e)
            return jsonify({'error': 'Database error'}), 500
        finally:
            if connection.is_connected():
                connection.close()
    else:
        return jsonify({'error': 'Failed to connect to database'}), 500




@app.route('/send_feedback', methods=['POST'])
def send_feedback():

    session_uuid = request.form.get('session_uuid')
    feedback = request.form.get('feedback', 'null')

    # Assume KFId is retrieved or generated here
    #kfid = request.form.get('kfid', 'KF102110000020')

    filename = os.path.join('chats', f"{session_uuid}_chats.json")
    connection = create_db_connection()
 #   if connection:
 #       try:
 #           update_query = """
 #           UPDATE ChatMessages
 #           SET MessageFeedback = %s
 #           WHERE ID = %s AND SessionUUID = %s;
 #           """
 #           cursor = connection.cursor()
 #           cursor.execute(update_query, (feedback, message_id, session_uuid))
 #           connection.commit()
 #           cursor.close()
 #       except Error as e:
 #           print(f"Error: {e}")
 #       finally:
 #           if connection.is_connected():
 #               connection.close()
    try:
        with open(filename, 'r+') as file:
            messages = json.load(file)

            if messages:
                messages[-1]['feedback'] = feedback  # Update the feedback
                file.seek(0)
                json.dump(messages, file)
                file.truncate()
            else:
                print("No messages found for user:", session_uuid)
            select_query = """
            SELECT MAX(ID) FROM ChatMessages
            WHERE SessionUUID = %s;
            """
            cursor = connection.cursor()
            cursor.execute(select_query, (session_uuid,))
            latest_message_id = cursor.fetchone()[0]
            if latest_message_id:
                update_query = """
                UPDATE ChatMessages
                SET MessageFeedback = %s
                WHERE ID = %s AND SessionUUID = %s;
                """
                cursor.execute(update_query, (feedback, latest_message_id, session_uuid))
                connection.commit()
            else:
                print(f"No messages found for session_uuid: {session_uuid}")

    except FileNotFoundError:
        print(f"No chat file found for user: {session_uuid}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {filename}")

    return jsonify({'status': 'Feedback received'})

@app.route('/login', methods=['POST'])
def login():
    MobileNumber = request.form.get('MobileNumber','null')
    kfid = get_next_kfid()
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            #insert_query = """INSERT INTO ChatMessages (SessionUUID, UserMessage, BotMessage, Language, KFId, CreatedDate, UserThread,MobileNumber)
                            #VALUES (%s, %s, %s, %s, %s,%s,%s,%s)"""
            # Assuming 'theUserInput' is the user message and 'response_message' is the bot response
            #cursor.execute(insert_query, (session_uuid, theUserInput, response_message,lang, kfid, input_time,activeUserThreadId))
            cursor.execute("INSERT INTO LoginDetails (KFId, MobileNumber) VALUES (%s, %s)", (kfid, MobileNumber))
            #update_message_count(connection, kfid, activeUserThreadId)
            #update_kfid_unique_thread_count(connection, kfid)
            connection.commit()
        except Error as e:
            print("Error while inserting into MySQL", e)
            return "Error while inserting into MySQL", 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
        return f"User created with KFId: {kfid}", 201
    else:
        return "Error connecting to the database", 500


@app.route('/send_message', methods=['POST'])
def send_message():
    print()
    print("Request data:", request.form)
    print()
    theUserInput = request.form.get('message')
    input_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("input_time 1: ",input_time)
    print()
    feedback = request.form.get('feedback', 'null')  # Default feedback to 'null'
    session_uuid = request.form.get('session_uuid')
    device_info = get_device_info()
    lang = request.form.get('language')
    kfid = request.form.get('kfid','null')
    MobileNumber = request.form.get('MobileNumber','null')
    web = request.form.get('web','null')
    #print("Device Information: ", kfid)
    print("theUserInput: ",theUserInput)
    print("session_uuid: ",session_uuid)
    print("lang: ",lang)
    #print("device_info: ",device_info)
    print("kfid: ",kfid)
    print("feedback: ",feedback)
    print("MobileNumber: ",MobileNumber)


    # Check if user exists and handle accordingly
    user_found = False
    with open('user.json', 'r') as file:
        user_data = json.load(file)

    for i in user_data:
        if i['session_uuid'] == session_uuid:
            user_found = True

            if len(i['thread']) < 1:
                thread = client.beta.threads.create()
                i['thread'] = thread.id
                i['timestamp_started'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                i['timestamp_ended'] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S")  # Initially empty, to be updated when conversation ends
                i['session_uuid'] = session_uuid
                with open('user.json', 'w') as file:
                    json.dump(user_data, file, indent=4)
            break
        else:
            print('User is: ',user_found)
    if not user_found:
        thread = client.beta.threads.create()
        add_new_user_to_json('user.json', thread.id,session_uuid)

    # Reload user_data to get the active thread ID and timestamps
    with open('user.json', 'r') as file:
        user_data = json.load(file)

    activeUserThreadId = ""
    for i in user_data:
        if i['session_uuid'] == session_uuid:
            activeUserThreadId = i['thread']

    message = client.beta.threads.messages.create(
            thread_id=activeUserThreadId,
            role="user",
            content=theUserInput
            )

    run = client.beta.threads.runs.create(
            thread_id=activeUserThreadId,
            assistant_id="asst_W9WA6vCaOCwxCRO2byOg6EgW",

            )

    while True:
        time.sleep(2)
        print("activeUserThreadId: ",activeUserThreadId)
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
                elif tool_call.function.name == "sales_predictor":
                    args = json.loads(tool_call.function.arguments)
                    location = args['location']
                    store_size = args['store_size']
                    area_type = args['area_type']
                    result = sales_predictor(location, area_type, store_size)
                    tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "output": result,
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

    response_message = response_message.replace("\n", "<br>")
    response_message = response_message.replace("<br>","\n")
    response_message = response_message.replace("**", "")

    # Enhance response using RAG
    # enhanced_response = enhance_response_with_rag(response_message)




    # Generate a unique filename
    # filename = os.path.join('chats', f"{theUser}_chats.json")
    # Get the current timestamp
    response_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conversation_data = {
            'input timestamp': input_time,
            'user_input': theUserInput,
            'response timestamp': response_time,
            'ai_response': response_message,
            'feedback': feedback
            }

    filename = os.path.join('chats', f"{session_uuid}_chats.json")

    try:
        # Check if file exists and has content
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'r+') as file:
                messages = json.load(file)
                messages.append(conversation_data)
                file.seek(0)
                json.dump(messages, file)
                file.truncate()
        else:
            # Create new file or overwrite empty file with a list containing the message
            with open(filename, 'w') as file:
                json.dump([conversation_data], file)
    except IOError as e:
        print(f"Error writing to file: {e}")

    # First, read the data from the file
    with open('user.json', 'r') as file:
        user_data = json.load(file)

    # Update the timestamp_ended for the specific user
    user_found = False
    for i in user_data:
        if i['session_uuid'] == session_uuid:
            i['timestamp_ended'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_found = True
            break

    # Then, write the updated data back to the file
    if user_found:
        with open('user.json', 'w') as file:
            json.dump(user_data, file, indent=4)
    else:
        print("User not found.")
    connection = create_db_connection()


    print()
    print("input_time: ",input_time)
    print()



    if connection:
        try:
            cursor = connection.cursor()
            insert_query = """
                INSERT INTO ChatMessages (SessionUUID, UserMessage, BotMessage, Language, KFId, CreatedDate, UserThread,MobileNumber,web)
                VALUES (%s, %s, %s, %s, %s,%s,%s,%s,%s)
            """
                # Assuming 'theUserInput' is the user message and 'response_message' is the bot response
            cursor.execute(insert_query, (session_uuid, theUserInput,response_message,lang, kfid, input_time,activeUserThreadId,MobileNumber,web))
            if web != "web":
                update_message_count(connection, kfid, activeUserThreadId)
                update_kfid_unique_thread_count(connection, kfid)
            connection.commit()
        except Error as e:
            print("Error while inserting into MySQL", e)
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return jsonify({'response': response_message})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
# %%
