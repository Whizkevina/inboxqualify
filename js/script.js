// script.js - FINAL VERSION

document.addEventListener('DOMContentLoaded', () => {
    const emailForm = document.getElementById('email-form');
    const resultsContainer = document.getElementById('results-container');
    // const apiEndpoint = 'http://127.0.0.1:8000/qualify'; // Our local backend server
    const apiEndpoint = 'https://inboxqualify-api.onrender.com/qualify'; // Our production backend server

    emailForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const subject = document.getElementById('subject').value;
        const emailBody = document.getElementById('email-body').value;

        if (!subject || !emailBody) {
            alert('Please fill out both the subject and email body.');
            return;
        }

        // Show loading state
        resultsContainer.innerHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <h3>Analyzing Your Email</h3>
                <p>AI is evaluating personalization, value proposition, and professionalism...</p>
            </div>
        `;

        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    subject: subject,
                    email_body: emailBody,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            console.error('Error fetching analysis:', error);
            resultsContainer.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">⚠️</div>
                    <h3>Analysis Failed</h3>
                    <p>Unable to connect to the analysis service. Please ensure the backend server is running and try again.</p>
                    <button type="button" class="retry-button" onclick="location.reload()">Try Again</button>
                </div>
            `;
        }
    });

    function displayResults(data) {
        resultsContainer.innerHTML = '';
        const card = document.createElement('div');
        card.className = 'results-card';
        card.innerHTML = `
            <div class="overall-score">
                <h3>${data.overallScore}/100</h3>
            </div>
            <p class="verdict">${data.verdict}</p>
            <div class="feedback-section">
                ${data.breakdown.map(category => `
                    <div class="category-score">
                        <div class="category-title">
                            <span>${category.name}</span>
                            <span>${category.score}/${category.maxScore}</span>
                        </div>
                        <p class="category-feedback">${category.feedback}</p>
                    </div>
                `).join('')}
            </div>
        `;
        resultsContainer.appendChild(card);
    }
});