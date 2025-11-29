document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const text = document.getElementById('text').value;
    if (!text.trim()) {
        showError('Please enter some text to analyze.');
        return;
    }
    
    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;
    
    // Show loading state
    document.querySelector('button[type="submit"]').disabled = true;
    hideError();
    hideResults();
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text,
                source_lang: sourceLang,
                target_lang: targetLang
            }),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Display results
        document.getElementById('results').style.display = 'block';
        
        // Display sentiment results
        const sentimentHtml = data.sentiment.error 
            ? `<span class="text-danger">Error: ${data.sentiment.error}</span>`
            : `Sentiment: ${data.sentiment.sentiment} (Score: ${data.sentiment.score.toFixed(2)})`;
        document.getElementById('sentimentResult').innerHTML = sentimentHtml;
        
        // Display translation results
        const translationHtml = data.translation.error
            ? `<span class="text-danger">Error: ${data.translation.error}</span>`
            : data.translation.text;
        document.getElementById('translationResult').innerHTML = translationHtml;
        
        // Display chat results
        const chatHtml = data.chat.error
            ? `<span class="text-danger">Error: ${data.chat.error}</span>`
            : data.chat.response;
        document.getElementById('chatResult').innerHTML = chatHtml;
        
        // Display performance metrics if available
        if (data.performance) {
            console.log('Performance:', data.performance);
        }
        
    } catch (error) {
        console.error('Error:', error);
        showError('An error occurred while processing your request. Please try again.');
    } finally {
        // Re-enable submit button
        document.querySelector('button[type="submit"]').disabled = false;
    }
});

function showError(message) {
    const errorDiv = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorDiv.style.display = 'block';
    document.getElementById('results').style.display = 'none';
}

function hideError() {
    document.getElementById('error').style.display = 'none';
}

function hideResults() {
    document.getElementById('results').style.display = 'none';
}

function showResults() {
    document.getElementById('results').style.display = 'block';
}