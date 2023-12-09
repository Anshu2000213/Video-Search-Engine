document.addEventListener('DOMContentLoaded', function() {
    console.log('lololo')
    // Fetch data from Flask route
    fetch('/get_user_history', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        const userHistoryList = document.getElementById('userHistoryList');
        data.history.forEach(item => {
            const listItem = document.createElement('li');
            listItem.className = 'user-history-item';
        
            const img = document.createElement('img');
            img.className = 'video-image';
            img.src = item.image;
            img.alt = item.title;
        
            const videoInfo = document.createElement('div');
            videoInfo.className = 'video-info';
        
            const title = document.createElement('p');
            title.className = 'video-title';
            title.textContent = item.title;
        
            videoInfo.appendChild(title);
            listItem.appendChild(img);
            listItem.appendChild(videoInfo);
            userHistoryList.appendChild(listItem);
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });
});


