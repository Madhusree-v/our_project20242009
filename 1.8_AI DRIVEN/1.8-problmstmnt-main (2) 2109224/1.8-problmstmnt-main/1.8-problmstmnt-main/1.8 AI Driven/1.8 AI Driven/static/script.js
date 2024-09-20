document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const searchForm = document.getElementById('search-form');
    const resultDiv = document.getElementById('result');
    const searchResultsDiv = document.getElementById('search-results');

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.json) {
                resultDiv.innerHTML = `<pre>${data.json}</pre>`;
            } else if (data.csv) {
                resultDiv.innerHTML = `<pre>${data.csv.replace(/\n/g, "<br>")}</pre>`;
            } else {
                resultDiv.innerHTML = `<pre>${data.text}</pre>`;
            }
        } else {
            resultDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
        }
    });

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = document.getElementById('search-input').value;

        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            searchResultsDiv.innerHTML = data.results.length > 0
                ? `<ul>${data.results.map(line => `<li>${line}</li>`).join('')}</ul>`
                : '<p>No results found.</p>';
        } else {
            searchResultsDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
        }
    });
});
