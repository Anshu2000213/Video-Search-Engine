// upload.js
function printError(e) {
    document.getElementById('uploadErrorText').textContent = e;
}

function printSuccess(text) {
    document.getElementById('uploadErrorText').textContent = text;
}

document.addEventListener('DOMContentLoaded', function () {
    var uploadForm = document.getElementById('uploadForm');
    // Add an event listener to the form
    uploadForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission
        // Get values from the form
        const videoTitle = document.getElementById('videoTitle').value;
        console.log(videoTitle)
        
        // Send a POST request to the upload_video route
        fetch('/upload_video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body:JSON.stringify({
                url: videoTitle,
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Handle the response from the server (if needed)
            if(data.status === 'success'){
                printSuccess(data.message)
            }else{
                printError(data.message)
            }
            console.log(data);
        })
        .catch(error => console.error('Error:', error));
    });
});