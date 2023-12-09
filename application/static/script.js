// script.js

// Set a cookie with the video ID
// document.cookie = 'currentVideoId=JipvyMu_X7bZXIYn';
// localStorage.setItem('liked', 'false');

function printError() {
    document.getElementById('loginErrorText').textContent = 'Invalid password.';
}

// login.js
// function likeVideo() {
//     alreadyLiked = localStorage.getItem('liked') === 'true';
//     likeCount = parseInt(document.getElementById('likeCount').textContent)

//     if (alreadyLiked) {
//         likeCount--;
//     } else {
//         likeCount++;
//     }

//     document.getElementById('likeCount').textContent = likeCount;

//     localStorage.setItem('liked', alreadyLiked ? 'false' : 'true');
// }

function attemptLogin() {
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;
    
    console.log(username, password)
    // Send a POST request to the server for authentication
    fetch("/authenticate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            username: username,
            password: password,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("Login Successful")
            // Redirect to the index page upon successful login
            window.location.href = "/index";
        } else {
            // Display login error message
            printError()
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
}

function displayVideo(videoInfo) {
    document.getElementById('likeCount').textContent = videoInfo.like_count;
    document.getElementById('actualTimestamp').textContent = videoInfo.timestamp.split('T')[0];
    document.getElementById('videoPlayer').src = `https://www.youtube.com/embed/${videoInfo.id}`;
    document.getElementById('actualViewCount').textContent = videoInfo.view_count;
    document.getElementById('actualCommentCount').textContent = videoInfo.comment_count;
    document.getElementById('actualVideoDescription').textContent = videoInfo.description;
}

function destroyComments(){
    document.getElementById('commentsContainer').textContent = '';
}

function destroyAndRecreateElement(elementId, imageId, paragraphId, parentElementId) {
    const parentElement = document.getElementById(parentElementId);
    const element = document.getElementById(elementId);

    // Remove the existing element if it exists
    if (element) {
        parentElement.removeChild(element);
    }

    // Create a new div element
    const newElement = document.createElement('div');
    newElement.id = elementId;

    // Create an img element
    const imgElement = document.createElement('img');
    imgElement.id = imageId; // Set the ID for the img element
    // You can set other attributes for the img element if needed, e.g., imgElement.src = 'path/to/image.jpg';

    // Create a p element
    const pElement = document.createElement('p');
    pElement.id = paragraphId; // Set the ID for the p element

    // Append the img and p elements to the new div element
    newElement.appendChild(imgElement);
    newElement.appendChild(pElement);

    // Append the new div element to the parent
    parentElement.appendChild(newElement);

    return newElement;
}

function updateVideo(index, image_url, title, id) {
    const thumbnailId = `thumbnail${index + 1}`;
    const titleId = `title${index + 1}`;
    const divId = `SRvideo_${index + 1}`;

    videoElement = destroyAndRecreateElement( `SRvideo_${index + 1}`,`thumbnail${index + 1}`, `title${index + 1}`, 'videosList');
    console.log(videoElement)
    // Update thumbnail image source
    document.getElementById(thumbnailId).src = image_url;
    // Update title text
    document.getElementById(titleId).textContent = title;
    // Add event listener to div
    // document.getElementById(divId).removeEventListener('click');
    const clickHandler = function () {
        const prev_video_id = '';
        document.getElementById('loader').style.display = 'block';
        document.getElementById('videosList').style.display = 'none';
        // Make an additional AJAX request to the Flask backend with the video information
        fetch('/new_video_click', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                videoId: id, // Replace 'videoId' with the actual property name
            }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Handle Click Data:', data);
            
            displayVideo(data.video_info);
            viewCount = parseInt(document.getElementById('actualViewCount').textContent)
            document.getElementById("actualViewCount").textContent = viewCount + 1
            if(data.video_info.is_liked[0] === 1){
                document.getElementById('likeButton').style.backgroundColor = 'lightgreen';
            }
            destroyComments();
            show_comments();
            prev_video_id = data.prev_video_id;
        })
        .catch(error => {
            console.error('Error:', error);
        });
        
        console.log(prev_video_id)
        fetch('/update_recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                videoId: id, // Replace 'videoId' with the actual property name
                prev_video_id: prev_video_id,
            }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Handle Click Data:', data);
        
            for (let i = 0; i < 10; i++) {
                updateVideo(i, data.recommendations[i].image, data.recommendations[i].title, data.recommendations[i].id);
            }

            document.getElementById('loader').style.display = 'none';
            document.getElementById('videosList').style.display = 'block';
        })
        .catch(error => {
            document.getElementById('loader').style.display = 'none';
            document.getElementById('videosList').style.display = 'block';
            console.error('Error:', error);
        });
    };
    // Remove previous event listener if exists
    videoElement.removeEventListener('click', clickHandler);
    
    // Add the new event listener
    videoElement.addEventListener('click', clickHandler);
    document.getElementById('countsContainer').style.display = 'block';
    console.log("SR Videos updated Successfully!");
}

function postComment(user_id, commentText) {
    // let username = 'aditya';
    if(commentText.trim() === ''){
        return;
    }

    var commentElement = document.createElement('p');

    var boldUsername = document.createElement('strong');
    boldUsername.textContent = `User ${user_id}: `;

    commentElement.appendChild(boldUsername);
    commentElement.appendChild(document.createTextNode(commentText));

    var commentsContainer = document.getElementById('commentsContainer');
    commentsContainer.insertBefore(commentElement, commentsContainer.firstChild);

    document.getElementById('enterComment').value = '';

    // document.getElementById('actualCommentCount').textContent++;
}

function show_comments(){
    // Send a POST request to the get_comment route
    fetch('/get_comments', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response from the server (if needed)
        console.log(data);
        for (let i = 0; i < data.comments.length; i++) {
            postComment(data.comments[i].Userid, data.comments[i].Texts);
        }
    })
    .catch(error => console.error('Error:', error));
}

document.addEventListener('DOMContentLoaded', function () {
    const searchButton = document.getElementById('searchButton');
    const searchResultsList = document.getElementById('searchResultsList');
    
    searchButton.addEventListener('click', function () {
        const searchQuery = document.getElementById('searchQuery').value;
        document.getElementById('loader').style.display = 'block';
        // Make an AJAX request to the Flask backend
        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'search_query': searchQuery,
            }),
        })
        .then(response => response.json())
        .then(data => {
            // // Clear previous search results
            // searchResultsList.innerHTML = '';
            // Handle the search results (update the UI as needed)
            document.getElementById('videosList').style.display = 'none';
            console.log(data)
            // Loop to update videos for thumbnails 1 to 10
            for (let i = 0; i < 10; i++) {
                updateVideo(i, data[i].image, data[i].title, data[i].id);
            }
            document.getElementById('loader').style.display = 'none';
            document.getElementById('videosList').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });

    document.getElementById('submitComment').addEventListener('click', function() {
        // Get the comment text from the input field
        const commentText = document.getElementById('enterComment').value;
        console.log(commentText)
        // Send a POST request to the add_comment route
        fetch('/add_comment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                commentText: commentText,
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Handle the response from the server (if needed)
            console.log(data);
            commentCount = parseInt(document.getElementById('actualCommentCount').textContent)
            document.getElementById("actualCommentCount").textContent = commentCount + 1
            postComment(data.user, data.comment);
        })
        .catch(error => console.error('Error:', error));
    });

    document.getElementById('upload_button').addEventListener('click', function() {
        window.location.href = "/upload";
    });

    document.getElementById('history_button').addEventListener('click', function() {
        window.location.href = "/history";
    });

    document.getElementById('toggleDarkMode').addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
    });

    document.getElementById('likeButton').addEventListener('click', function () {
        localStorage.setItem('liked', 'false');
        
        fetch('/like_button', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            // Handle the response from the server (if needed)
            console.log(data)
            if(data.status === "liked"){
                likeCount = parseInt(document.getElementById('likeCount').textContent)
                document.getElementById('likeCount').textContent = likeCount + 1;
                document.getElementById('likeButton').style.backgroundColor = 'lightgreen';
            }else if(data.status === "disliked"){
                likeCount = parseInt(document.getElementById('likeCount').textContent)
                document.getElementById('likeCount').textContent = likeCount - 1;
                document.getElementById('likeButton').style.backgroundColor = 'grey';
            }else{
                console.log(data)
            }
        })
        .catch(error => console.error('Error:', error));
    });
});