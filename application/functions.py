from application import app, mysql, db, api_key, video_list
from flask import jsonify, session
from datetime import datetime
import copy
import json
from bson import BSON
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs

# # Initialize the MySQL database
# def init_db():
#     with app.app_context():
#         cursor = mysql.connection.cursor()
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS User_Table (
#                 User_id Varchar(50),
#                 Video_id Varchar(50),
#                 Timestamp DATETIME,
#                 Counter INT,
#                 PRIMARY KEY (User_id, Video_id)
#             )
#         ''')
#         cursor.close()

def get_videos():
    global video_list
    col = db["videos"]
    
    videos = []
    for x in col.find({}): 
        videos.append(x)
    
    return videos
    
    videos_count = col.count_documents({})
    
    if('videos_count' not in session):
        session['videos_count'] = videos_count
        if(len(video_list) == 0):
            videos = []
            for x in col.find({}): 
                videos.append(x)
            video_list = copy.deepcopy(videos)
            return video_list
        else:
            return video_list
    else:
        if(session['videos_count']  == videos_count and session['videos_count'] > 0 and len(video_list) != 0):
            return video_list
        else:
            videos = []
            for x in col.find({}): 
                videos.append(x)
            video_list = copy.deepcopy(videos)
            return video_list

# Function to update data in the table
def update_data(user_id, video_id):
    with app.app_context():
        cursor = mysql.connection.cursor()
        
        # Check if the entry exists
        cursor.execute('''
            SELECT * FROM User_Table WHERE User_id = %s AND Video_id = %s
        ''', (user_id, video_id))
        existing_entry = cursor.fetchone()

        if existing_entry:
            # If entry exists, update the counter and timestamp
            cursor.execute('''
                UPDATE User_Table SET Counter = Counter + 1, Timestamp = %s
                WHERE User_id = %s AND Video_id = %s
            ''', (datetime.now(), user_id, video_id))
        else:
            # If entry doesn't exist, add a new entry with counter=1 and timestamp
            cursor.execute('''
                INSERT INTO User_Table (User_id, Video_id, Timestamp, Counter)
                VALUES (%s, %s, %s, 1)
            ''', (user_id, video_id, datetime.now()))

        mysql.connection.commit()
        cursor.close()

# def init_user_db():
#     with app.app_context():
#         cursor = mysql.connection.cursor()
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS User_Table_Information (
#                 User_id INT AUTO_INCREMENT,
#                 Email_id VARCHAR(50),
#                 Password VARCHAR(50),
#                 PRIMARY KEY (User_id),
#                 UNIQUE KEY (Email_id)
#             )
#         ''')
#         mysql.connection.commit() 
#         cursor.close()


def check_email(email, password):
    with app.app_context():
        cursor = mysql.connection.cursor()

        # Check if the email exists in the User_Table_Information
        cursor.execute('''
            SELECT User_id, Password FROM User_Table_Information WHERE Email_id = %s
        ''', (email,))
        result = cursor.fetchone()

        if result:
            # If the email exists, check the password
            if result[1] == password:
                # Password is correct
                cursor.close()
                return result[0]  # Returning User_id or any other relevant information
            else:
                # Password is incorrect
                cursor.close()
                return None  # You can also return an error message here if you prefer
        else:
            # If the email doesn't exist, create a new entry
            cursor.execute('''
                INSERT INTO User_Table_Information (Email_id, Password)
                VALUES (%s, %s)
            ''', (email, password))

            cursor.execute('SELECT LAST_INSERT_ID()')
            new_user_id = cursor.fetchone()[0]

            mysql.connection.commit()
            cursor.close()
            return new_user_id 

# Function to handle the specified tasks
def Top_5_Recent_Videos(user_id):
    with app.app_context():
        cur = mysql.connection.cursor()
        query = "SELECT Video_id FROM User_Table WHERE User_id = %s ORDER BY Timestamp DESC LIMIT 5"
        cur.execute(query, (user_id,))
        results = cur.fetchall()
        
        # Closing the cursor
        mysql.connection.commit()
        cur.close()
        return results

# Function to handle the specified tasks
def getUserHistory(user_id):
    with app.app_context():
        cur = mysql.connection.cursor()
        query = "SELECT Video_id FROM User_Table WHERE User_id = %s ORDER BY Timestamp DESC"
        cur.execute(query, (user_id,))
        results = cur.fetchall()
        
        # Closing the cursor
        mysql.connection.commit()
        cur.close()
        return results


def Top_5_Counter(user_id):
    with app.app_context():
        cur = mysql.connection.cursor()
        query = "SELECT Video_id FROM User_Table WHERE User_id = %s ORDER BY Counter DESC LIMIT 5"
        cur.execute(query, (user_id,))
        results = cur.fetchall()
        
        # Closing the cursor
        mysql.connection.commit()
        cur.close()
        return results

def extract_video_id(video_url):
    parsed_url = urlparse(video_url)
    query_params = parse_qs(parsed_url.query)
    video_id = query_params.get('v', [None])[0]
    return video_id

def get_video_info(video_id):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.videos().list(part='snippet,statistics,contentDetails', id=video_id)
        response = request.execute()
        return response['items'][0] if 'items' in response else None
    except Exception as e:
        return e

def create_json(video_info):
    try:
        if not video_info:
            return None

        snippet = video_info['snippet']
        content_details = video_info['contentDetails']
        statistics = video_info['statistics']

        formatted_data = {
            "videoInfo": {
                "kind": video_info['kind'],
                "id": video_info['id'],
                "etag": video_info['etag'],
                "snippet": {
                    "thumbnails": snippet['thumbnails'],
                    "title": snippet['title'],
                    "defaultAudioLanguage": snippet.get('defaultAudioLanguage'),
                    "localized": {
                        "description": snippet.get('description'),
                        "title": snippet.get('title')
                    },
                    "channelId": snippet.get('channelId'),
                    "publishedAt": snippet.get('publishedAt'),
                    "liveBroadcastContent": snippet.get('liveBroadcastContent'),
                    "channelTitle": snippet.get('channelTitle'),
                    "categoryId": snippet.get('categoryId'),
                    "tags": snippet.get('tags', []),
                    "description": snippet.get('description')
                },
                "statistics": {
                    "commentCount": statistics.get('commentCount', 0),
                    "viewCount": statistics.get('viewCount', 0),
                    "favoriteCount": statistics.get('favoriteCount', 0),
                    "dislikeCount": statistics.get('dislikeCount', 0),
                    "likeCount": statistics.get('likeCount', 0)
                },
                "recordingDetails": {
                    "recordingDate": content_details.get('recordingDate')
                }
            }
    }
    except Exception as e:
        return e

    return formatted_data

def insert_document(data):
    try:
        collection = db["videos"]
        # data = BSON.encode(data)
        # print (bson_example)
        # print (type(bson_example))  
        # Insert the document into the MongoDB collection
        result = collection.insert_one(data)
        
        # Check if the document was successfully inserted
        if result.inserted_id:
            return jsonify({'status': 'success', 'message': 'Document inserted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to insert document'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def increase_viewCount(videoId):
    try:
        col = db["videos"]
        # Update the document to increment the viewCount field
        col.update_one(
            {"videoInfo.id": videoId},
            [
                {"$set": {"videoInfo.statistics.viewCount": {"$toInt": "$videoInfo.statistics.viewCount"}}},
                {"$set": {"videoInfo.statistics.viewCount": {"$add": ["$videoInfo.statistics.viewCount", 1]}}}
            ]
        )
    except Exception as e:
        return e

def increase_commentCount(videoId):
    try:
        col = db["videos"]
        # Update the document to increment the viewCount field
        col.update_one(
            {"videoInfo.id": videoId},
            [
                {"$set": {"videoInfo.statistics.commentCount": {"$toInt": "$videoInfo.statistics.commentCount"}}},
                {"$set": {"videoInfo.statistics.commentCount": {"$add": ["$videoInfo.statistics.commentCount", 1]}}}
            ]
        )
    except Exception as e:
        return e

def increase_likeCount(videoId):
    try:
        col = db["videos"]
        # Update the document to increment the viewCount field
        col.update_one(
            {"videoInfo.id": videoId},
            [
                {"$set": {"videoInfo.statistics.likeCount": {"$toInt": "$videoInfo.statistics.likeCount"}}},
                {"$set": {"videoInfo.statistics.likeCount": {"$add": ["$videoInfo.statistics.likeCount", 1]}}}
            ]
        )
    except Exception as e:
        return e

def increase_dislikeCount(videoId):
    try:
        col = db["videos"]
        # Update the document to increment the viewCount field
        col.update_one(
            {"videoInfo.id": videoId},
            [
                {"$set": {"videoInfo.statistics.dislikeCount": {"$toInt": "$videoInfo.statistics.dislikeCount"}}},
                {"$set": {"videoInfo.statistics.dislikeCount": {"$add": ["$videoInfo.statistics.dislikeCount", 1]}}}
            ]
        )
    except Exception as e:
        return e

def decrease_likeCount(videoId):
    try:
        col = db["videos"]
        # Update the document to increment the viewCount field
        col.update_one(
            {"videoInfo.id": videoId},
            [
                {"$set": {"videoInfo.statistics.likeCount": {"$toInt": "$videoInfo.statistics.likeCount"}}},
                {"$set": {"videoInfo.statistics.likeCount": {"$subtract": ["$videoInfo.statistics.likeCount", 1]}}}
            ]
        )
    except Exception as e:
        return e

def decrease_dislikeCount(videoId):
    try:
        col = db["videos"]
        # Update the document to increment the viewCount field
        col.update_one(
            {"videoInfo.id": videoId},
            [
                {"$set": {"videoInfo.statistics.dislikeCount": {"$toInt": "$videoInfo.statistics.dislikeCount"}}},
                {"$set": {"videoInfo.statistics.dislikeCount": {"$subtract": ["$videoInfo.statistics.dislikeCount", 1]}}}
            ]
        )
    except Exception as e:
        return e

def isLiked(video_id, user_id):
    with app.app_context():
        cursor = mysql.connection.cursor()

        # Check if the user has already liked the video
        cursor.execute('SELECT likes FROM User_Table WHERE video_id = %s AND user_id = %s', (video_id, user_id))
        result = cursor.fetchone()

        return result

def like(video_id, user_id):
    with app.app_context():
        cursor = mysql.connection.cursor()

        # Check if the user has already liked the video
        cursor.execute('SELECT likes FROM User_Table WHERE video_id = %s AND user_id = %s', (video_id, user_id))
        result = cursor.fetchone()

        if int(list(result)[0])==1:
            # If the user has already liked the video, do nothing
            return "User already liked this video."

        # If the user has not liked the video, update the 'likes' column
        cursor.execute('UPDATE User_Table SET likes = 1 WHERE video_id = %s AND user_id = %s', (video_id, user_id))
        mysql.connection.commit()
        cursor.close()

        return "Like added successfully"

def dis_like(video_id, user_id):
    with app.app_context():
        cursor = mysql.connection.cursor()

        # Check if the user has already liked the video
        cursor.execute('SELECT likes FROM User_Table WHERE video_id = %s AND user_id = %s', (video_id, user_id))
        result = cursor.fetchone()

        if int(list(result)[0])==2:
            # If the user has already liked the video, do nothing
            return "User already  Disliked this video."

        # If the user has not liked the video, update the 'likes' column
        cursor.execute('UPDATE User_Table SET likes = likes - 1 WHERE video_id = %s AND user_id = %s', (video_id, user_id))
        mysql.connection.commit()
        cursor.close()

        return "Disliked added successfully."
