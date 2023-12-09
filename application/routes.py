from application import app, db, neo_driver
from application.functions import update_data, check_email, Top_5_Recent_Videos, Top_5_Counter, get_videos, getUserHistory, extract_video_id, get_video_info, create_json, insert_document 
from application.functions import increase_viewCount, increase_commentCount, increase_likeCount, increase_dislikeCount, decrease_likeCount, decrease_dislikeCount, isLiked, like, dis_like 
from flask import render_template, request, jsonify, session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Index route so that when we launch our application we do not get a 404 error.
@app.route('/')
def login():
    # return render_template('index.html')
    if 'user_id' in session:
        session['curr_video_id'] = ''
        print(session['user_id'])
        return render_template('index.html')
    else:
        return render_template('login.html')

@app.route('/index')
def index():
    session['curr_video_id'] = ''
    print(session['user_id'])
    return render_template('index.html')


def calculate_similarity(query, video):
    if('tags' in video):
        # Concatenate title, description, and tags into a single string
        video_text = f"{video['videoInfo']['snippet']['title']} {video['videoInfo']['snippet']['description']} {' '.join(video['videoInfo']['snippet']['tags'])}"
    else:
        # Concatenate title, description into a single string
        video_text = f"{video['videoInfo']['snippet']['title']} {video['videoInfo']['snippet']['description']}"

    # Create a TfidfVectorizer
    vectorizer = TfidfVectorizer()

    # Fit and transform the vectorizer on the query and video text
    tfidf_matrix = vectorizer.fit_transform([query, video_text])

    # Calculate cosine similarity between the query and video
    similarity_score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

    return similarity_score

@app.route('/search', methods=['POST'])
def search():
    videos = get_videos()
    
    #print(videos[0]['videoInfo']['snippet']['tags'])
    search_query = request.form.get('search_query')

    # Calculate similarity scores for each video
    results = []
    for video in videos:
        similarity_score = calculate_similarity(search_query, video)
        results.append({'video': video, 'similarity_score': similarity_score})

    # Sort results by similarity_score in descending order
    results = sorted(results, key=lambda x: x['similarity_score'], reverse=True)
    
    # print(results[0])
    search_res = []
    for res in results[:10]:
        search_res.append({'image': res['video']['videoInfo']['snippet']['thumbnails']['default']['url'], 'id':res['video']['videoInfo']['id'], 'title': res['video']['videoInfo']['snippet']['title'], 'similarity_score': res['similarity_score']})
    
    for res in results[:10]:
        print(res['video']['videoInfo']['id'])
    # # Return top 5 results as JSON
    return jsonify(search_res)

@app.route('/new_video_click', methods=['POST'])
def new_video_click():
    current_video_id = None
    collection = db["videos"]
    
    if(session['curr_video_id'] != ''):
        current_video_id = session['curr_video_id']
    
    # Get the video ID of the clicked video from the request
    clicked_video_id = request.json.get('videoId')
    
    hasLiked = isLiked(clicked_video_id, session['user_id'])
    print(increase_viewCount(clicked_video_id))
    
    print("new_video_clicked", current_video_id, clicked_video_id)
    
    # Find the document based on clicked_video_info
    vid_info_fromDb = collection.find_one({'videoInfo.id': clicked_video_id})
    
    clicked_video_info = {'like_count': vid_info_fromDb['videoInfo']['statistics']['likeCount'], 'id': vid_info_fromDb['videoInfo']['id'],'view_count' : vid_info_fromDb['videoInfo']['statistics']['viewCount'], 'comment_count': vid_info_fromDb['videoInfo']['statistics']['commentCount'], 'description': vid_info_fromDb['videoInfo']['snippet']['localized']['description'], 'title': vid_info_fromDb['videoInfo']['snippet']['localized']['title'], 'timestamp': vid_info_fromDb['videoInfo']['snippet']['publishedAt'], 'is_liked': hasLiked}

    session['curr_video_id'] = clicked_video_id
    return jsonify({'video_info': clicked_video_info, 'prev_video_id': current_video_id})

@app.route('/update_recommendations', methods=['POST'])
def update_recommendations():
    current_video_id = None
    collection = db["videos"]
    
    # if(session['curr_video_id'] != ''):
    #     current_video_id = session['curr_video_id']
    
    # Get the video ID of the clicked video from the request
    clicked_video_id = request.json.get('videoId')
    
    current_video_id = request.json.get('prev_video_id')
    
    print("update_recommendation", current_video_id, clicked_video_id)
    
    # Find the document based on clicked_video_info
    vid_info_fromDb = collection.find_one({'videoInfo.id': clicked_video_id})
    
    clicked_video_info =  vid_info_fromDb['videoInfo']['snippet']['localized']['title']
    
    print(clicked_video_info)
    if(current_video_id):
        with neo_driver.session() as neo_session:
            query = (
                f"MATCH (video1:Video {{id: '{current_video_id}'}}) "
                f"MATCH (video2:Video {{id: '{clicked_video_id}'}}) "
                "MERGE (video1)-[rel:connected_to]-(video2) "
                "ON CREATE SET rel.weight = 1 "
                "ON MATCH SET rel.weight = rel.weight + 1"
            )

            neo_session.run(query)

            print("Connection updated successfully")

    update_data(session["user_id"], clicked_video_id)

    recommendations = []
            
    with neo_driver.session() as neo_session:
        # Cypher query to retrieve the top 5 connected videos based on weights
        query = (
            f"MATCH (:Video {{id: '{clicked_video_id}'}})-[r:connected_to]->(otherVideo:Video) "
            "RETURN otherVideo, r.weight "
            "ORDER BY r.weight DESC "
            "LIMIT 5"
        )
        result = neo_session.run(query)

        # Extracting the relevant information from the Neo4j Node objects
        top_videos = [[record['otherVideo']['id'],record['r.weight']] for record in result]

        top_videos = sorted(top_videos, key=lambda x:x[1])

        for neo_videos in top_videos[:4]:
            recommendations.append(neo_videos[0])
    
    sql_recommendations = []
    user_history_info = ''
    sql_vid_recent = list(Top_5_Recent_Videos(session['user_id']))[:2]
    for sql_vid in sql_vid_recent:
        sql_vid_info = collection.find_one({'videoInfo.id': list(sql_vid)[0]})['videoInfo']['snippet']['localized']['description']
        user_history_info += (sql_vid_info + ' ')
    
    sql_vid_counter = list(Top_5_Counter(session['user_id']))[:2]
    for sql_vid in sql_vid_counter:
        sql_vid_info = collection.find_one({'videoInfo.id': list(sql_vid)[0]})['videoInfo']['snippet']['localized']['description']
        user_history_info += (sql_vid_info + ' ')

    videos = get_videos()
    
    for video in videos:
        if(video['videoInfo']['id'] != clicked_video_id and not any(video['videoInfo']['id'] in inner_list[0] for inner_list in sql_recommendations)
):
            similarity_score = calculate_similarity(user_history_info, video)
            sql_recommendations.append([video['videoInfo']['id'],similarity_score])
    
    sql_recommendations = sorted(sql_recommendations, key=lambda x:x[1])
    
    for sql_videos in sql_recommendations[:4]:
            recommendations.append(sql_videos[0])
            
    videos = get_videos()
    title_rc_count = 0
    for video in videos:
        if(video['videoInfo']['id'] != clicked_video_id):
            similarity_score = calculate_similarity(clicked_video_info, video)
            recommendations.append(video['videoInfo']['id'])
            title_rc_count += 1
            print(video['videoInfo']['snippet']['localized']['title'], similarity_score)
            if(len(recommendations) == 10):
                break

    recommendations_info = []
    for vid in recommendations:
        vid_info = collection.find_one({'videoInfo.id': vid})
        recommendations_info.append({'image': vid_info['videoInfo']['snippet']['thumbnails']['default']['url'], 'id':vid_info['videoInfo']['id'], 'title': vid_info['videoInfo']['snippet']['title']})
    
    print(recommendations)
    return jsonify({"recommendations": recommendations_info})

@app.route('/add_comment', methods=['POST'])
def add_comment():
    user_id = session['user_id']
    current_video_id = session['curr_video_id']
    
    comment  = request.json.get('commentText')
    print(increase_commentCount(current_video_id))
    print(user_id, current_video_id, comment)
    with neo_driver.session() as neo_session:
        query = (
            f"MATCH (video1:Video {{id:'{current_video_id}'}}) "
            f"CREATE (comment:Comment{{Texts:'{comment}', Userid:'{user_id}'}})"
            "CREATE (comment)-[:COMMENT_ON]->(video1) "
            "RETURN comment, video1"
        )
        result = neo_session.run(query)
        record = result.single()
        comment_properties = dict(record['comment'].items())
        video_properties = dict(record['video1'].items())
        return jsonify({"message": "Comment added successfully", "comment": comment_properties, "user": user_id, "video": video_properties, "comment": comment})


@app.route('/get_comments', methods=['POST'])
def get_comments():
    current_video_id = session['curr_video_id']
    with neo_driver.session() as neo_session:
        query = (
            "MATCH (c:Comment)-[:COMMENT_ON]->(video1:Video {id: $videoid})"
            "RETURN c, video1"
        )
        result = neo_session.run(query, videoid=current_video_id)

        comments = []
        for record in result:
            comment_properties = dict(record['c'].items())
            comments.append(comment_properties)

        if comments:
            print(comments)
            return jsonify({"comments": comments})
        else:
            return jsonify({"error": "No comments found for the specified video ID"})

@app.route('/get_user_history', methods=['POST'])
def get_user_history():
    print(session['user_id'])
    collection = db["videos"]
    sql_vid_recent = list(getUserHistory(session['user_id']))
    
    history = []
    
    for vid_id in sql_vid_recent:
        history.append(list(vid_id)[0])
    
    history_info = []
    for vid in history:
        vid_info = collection.find_one({'videoInfo.id': vid})
        history_info.append({'image': vid_info['videoInfo']['snippet']['thumbnails']['default']['url'], 'id':vid_info['videoInfo']['id'], 'title': vid_info['videoInfo']['snippet']['title']})
    
    return jsonify({"history": history_info})
    
@app.route('/authenticate', methods=['POST'])
def authenticate():
    email = request.json.get('username')
    password = request.json.get('password')    

    # Authenticate user using sql database
    user_id = check_email(email, password)
    print(user_id)
    if user_id is not None:
        session['user_id'] = user_id
        return jsonify({'success': True})
    else:
        # Handle authentication failure (you might want to show an error message)
        return jsonify({'success': False})

@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        youtube_url = request.json.get('url')
        video_id = extract_video_id(youtube_url)
        video_info = get_video_info(video_id)
        json_data = create_json(video_info)
        videoid = json_data['videoInfo']['id']
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to insert document'})
    
    print(videoid)
    
    with neo_driver.session() as neo_session:
        query = (
            "CREATE (a:Video {id: $videoid})"
            "RETURN a"
        )
        result = neo_session.run(query, videoid=videoid)

        # Extracting the created video node properties
        record = result.single()
        video_properties = dict(record['a'].items())

    return insert_document(json_data)

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/like_button', methods=['POST'])
def like_button():
    user_id = session['user_id']
    curr_video_id = session['curr_video_id']
    has_user_liked = isLiked(curr_video_id, user_id)
    has_user_liked = int(list(has_user_liked)[0])
    print(has_user_liked)
    if(has_user_liked == 0):
        like(curr_video_id, user_id)
        print(increase_likeCount(curr_video_id))
        return jsonify({'status': 'liked'})
    elif(has_user_liked == 1):
        dis_like(curr_video_id, user_id)
        print(decrease_likeCount(curr_video_id))
        increase_dislikeCount(curr_video_id)
        return jsonify({'status': 'disliked'})
    elif(has_user_liked == 2):
        like(curr_video_id, user_id)
        print(decrease_dislikeCount(curr_video_id))
        increase_likeCount(curr_video_id)
        return jsonify({'status': 'liked'})
    else:
        return jsonify({'status': 'Error'})