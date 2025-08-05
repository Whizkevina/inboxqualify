// script.js - ENHANCED VERSION WITH QUICK WINS

document.addEventListener('DOMContentLoaded', () => {
    const emailForm = document.getElementById('email-form');
    const resultsContainer = document.getElementById('results-container');
    
    // Use the API configuration for endpoints
    const apiEndpoint = API_CONFIG.getURL('/qualify');

    // === QUICK WINS FEATURES ===
    
    // 1. Initialize Character Counters
    initializeCharacterCounters();
    
    // 2. Initialize Quick Templates
    initializeQuickTemplates();
    
    // 3. Initialize Dark Mode
    initializeDarkMode();
    
    // 4. Initialize Email Preview
    initializeEmailPreview();
    
    // 5. Initialize Export Features
    initializeExportFeatures();

    // === ORIGINAL EMAIL ANALYSIS FUNCTIONALITY ===
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
        
        // Show export section after results are displayed
        const exportSection = document.getElementById('export-section');
        if (exportSection) {
            exportSection.classList.add('show');
        }
    }

    // === QUICK WINS FEATURE IMPLEMENTATIONS ===

    // 1. Character Counter Implementation
    function initializeCharacterCounters() {
        const subjectInput = document.getElementById('subject');
        const bodyTextarea = document.getElementById('email-body');
        const subjectCounter = document.getElementById('subject-counter');
        const bodyCounter = document.getElementById('body-counter');

        if (subjectInput && subjectCounter) {
            subjectInput.addEventListener('input', function() {
                const length = this.value.length;
                subjectCounter.textContent = length;
                
                const counterDiv = subjectCounter.closest('.character-counter');
                counterDiv.classList.remove('warning', 'error');
                
                if (length < 30 || length > 50) {
                    counterDiv.classList.add('warning');
                }
                if (length > 70) {
                    counterDiv.classList.add('error');
                }
            });
        }

        if (bodyTextarea && bodyCounter) {
            bodyTextarea.addEventListener('input', function() {
                const length = this.value.length;
                const wordCount = this.value.trim().split(/\s+/).filter(word => word.length > 0).length;
                bodyCounter.textContent = `${length} chars (${wordCount} words)`;
                
                const counterDiv = bodyCounter.closest('.character-counter');
                counterDiv.classList.remove('warning', 'error');
                
                if (wordCount < 50 || wordCount > 200) {
                    counterDiv.classList.add('warning');
                }
                if (wordCount > 300) {
                    counterDiv.classList.add('error');
                }
            });
        }
    }

    // 2. Quick Templates Implementation
    function initializeQuickTemplates() {
        const templateButtons = document.querySelectorAll('.template-btn');
        const subjectInput = document.getElementById('subject');
        const bodyTextarea = document.getElementById('email-body');

        const templates = {
            'cold-outreach': {
                subject: 'Quick partnership opportunity - [Your Company]',
                body: `Hi [First Name],

I noticed [specific detail about their company/recent achievement] and was impressed by [specific compliment].

I'm [your name] from [your company]. We help [brief value proposition] and I think there might be a great opportunity for us to collaborate.

Would you be open to a brief 15-minute call this week to discuss how we could potentially work together?

Best regards,
[Your name]`
            },
            'follow-up': {
                subject: 'Following up on our conversation',
                body: `Hi [First Name],

I wanted to follow up on our conversation from [mention when/where you met or spoke].

As discussed, I think [briefly restate the value proposition or next step] could be really valuable for [their company/situation].

Would you have 15 minutes this week for a quick call to explore this further?

Looking forward to hearing from you.

Best,
[Your name]`
            },
            'introduction': {
                subject: 'Introduction from [Mutual Connection Name]',
                body: `Hi [First Name],

[Mutual connection name] suggested I reach out to you regarding [specific reason for introduction].

I'm [your name] from [your company], and we specialize in [brief description of what you do]. [Mutual connection] thought you might be interested in [specific value proposition].

Would you be open to a brief conversation to see if there's a potential fit?

Best regards,
[Your name]`
            },
            'partnership': {
                subject: 'Partnership proposal - [Your Company] x [Their Company]',
                body: `Hi [First Name],

I've been following [their company] and am really impressed by [specific achievement or aspect of their business].

At [your company], we [brief description of what you do], and I believe there's a great opportunity for our companies to collaborate.

Specifically, I think we could [outline potential partnership opportunity] which would benefit both our customers.

Would you be interested in exploring this further? I'd love to set up a brief call to discuss the possibilities.

Best regards,
[Your name]`
            }
        };

        templateButtons.forEach(button => {
            button.addEventListener('click', function() {
                const templateType = this.getAttribute('data-template');
                const template = templates[templateType];
                
                if (template && subjectInput && bodyTextarea) {
                    subjectInput.value = template.subject;
                    bodyTextarea.value = template.body;
                    
                    // Trigger character counter updates
                    subjectInput.dispatchEvent(new Event('input'));
                    bodyTextarea.dispatchEvent(new Event('input'));
                    
                    // Update preview if visible
                    updateEmailPreview();
                    
                    // Visual feedback
                    this.style.background = 'var(--success)';
                    this.style.color = 'white';
                    setTimeout(() => {
                        this.style.background = '';
                        this.style.color = '';
                    }, 1000);
                }
            });
        });
    }

    // 3. Dark Mode Implementation
    function initializeDarkMode() {
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        const savedTheme = localStorage.getItem('theme') || 'light';
        
        // Apply saved theme
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateDarkModeButton(savedTheme);

        if (darkModeToggle) {
            darkModeToggle.addEventListener('click', function(e) {
                e.preventDefault();
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                updateDarkModeButton(newTheme);
            });
        }
    }

    function updateDarkModeButton(theme) {
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            darkModeToggle.textContent = theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
        }
    }

    // 4. Email Preview Implementation
    function initializeEmailPreview() {
        const toggleButton = document.getElementById('toggle-preview');
        const subjectInput = document.getElementById('subject');
        const bodyTextarea = document.getElementById('email-body');

        if (toggleButton) {
            toggleButton.addEventListener('click', function() {
                const previewDiv = document.getElementById('email-preview');
                if (previewDiv.classList.contains('show')) {
                    previewDiv.classList.remove('show');
                    this.textContent = '👁️ Show Preview';
                } else {
                    previewDiv.classList.add('show');
                    this.textContent = '👁️ Hide Preview';
                    updateEmailPreview();
                }
            });
        }

        // Update preview when typing
        if (subjectInput && bodyTextarea) {
            [subjectInput, bodyTextarea].forEach(element => {
                element.addEventListener('input', updateEmailPreview);
            });
        }
    }

    function updateEmailPreview() {
        const subjectInput = document.getElementById('subject');
        const bodyTextarea = document.getElementById('email-body');
        const previewSubject = document.getElementById('preview-subject-text');
        const previewBody = document.getElementById('preview-body-text');

        if (previewSubject && subjectInput) {
            previewSubject.textContent = subjectInput.value || '[No subject]';
        }
        
        if (previewBody && bodyTextarea) {
            previewBody.textContent = bodyTextarea.value || '[No content]';
        }
    }

    // 5. Export Features Implementation
    function initializeExportFeatures() {
        const exportPdfBtn = document.getElementById('export-pdf');
        const exportHtmlBtn = document.getElementById('export-html');
        const copyResultsBtn = document.getElementById('copy-results');

        if (exportPdfBtn) {
            exportPdfBtn.addEventListener('click', exportAsPDF);
        }

        if (exportHtmlBtn) {
            exportHtmlBtn.addEventListener('click', exportAsHTML);
        }

        if (copyResultsBtn) {
            copyResultsBtn.addEventListener('click', copyResults);
        }
    }

    function exportAsPDF() {
        // For now, we'll create a printable version
        const resultsContent = document.getElementById('results-container').innerHTML;
        const subjectValue = document.getElementById('subject').value;
        const bodyValue = document.getElementById('email-body').value;
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>InboxQualify Analysis Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }
                    .email-content { background: #f9fafb; padding: 15px; border-radius: 8px; margin: 15px 0; }
                    .results { margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>InboxQualify Analysis Report</h1>
                    <p>Generated on: ${new Date().toLocaleDateString()}</p>
                </div>
                <div class="email-content">
                    <h3>Email Subject:</h3>
                    <p>${subjectValue}</p>
                    <h3>Email Body:</h3>
                    <p style="white-space: pre-wrap;">${bodyValue}</p>
                </div>
                <div class="results">
                    <h3>Analysis Results:</h3>
                    ${resultsContent}
                </div>
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    function exportAsHTML() {
        const resultsContent = document.getElementById('results-container').innerHTML;
        const subjectValue = document.getElementById('subject').value;
        const bodyValue = document.getElementById('email-body').value;
        
        const htmlContent = `<!DOCTYPE html>
<html>
<head>
    <title>InboxQualify Analysis Report</title>
    <style>
        body { font-family: 'Inter', Arial, sans-serif; margin: 40px; line-height: 1.6; color: #374151; }
        .header { border-bottom: 2px solid #667eea; padding-bottom: 20px; margin-bottom: 30px; }
        .email-content { background: #f9fafb; padding: 20px; border-radius: 12px; margin: 20px 0; border: 1px solid #e5e7eb; }
        .results { margin-top: 30px; }
        h1 { color: #667eea; }
        h3 { color: #374151; margin-top: 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📧 InboxQualify Analysis Report</h1>
        <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
    </div>
    <div class="email-content">
        <h3>📝 Email Subject:</h3>
        <p><em>${subjectValue}</em></p>
        <h3>📄 Email Body:</h3>
        <div style="white-space: pre-wrap; background: white; padding: 15px; border-radius: 8px; border: 1px solid #d1d5db;">${bodyValue}</div>
    </div>
    <div class="results">
        <h3>📊 Analysis Results:</h3>
        ${resultsContent}
    </div>
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; color: #6b7280;">
        <p>Powered by InboxQualify - AI Email Analysis</p>
    </footer>
</body>
</html>`;
        
        const blob = new Blob([htmlContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `inboxqualify-analysis-${new Date().toISOString().split('T')[0]}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function copyResults() {
        const subjectValue = document.getElementById('subject').value;
        const bodyValue = document.getElementById('email-body').value;
        const resultsContainer = document.getElementById('results-container');
        
        let resultsText = '';
        try {
            const resultsCard = resultsContainer.querySelector('.results-card');
            if (resultsCard) {
                const score = resultsCard.querySelector('.overall-score h3')?.textContent || 'N/A';
                const verdict = resultsCard.querySelector('.verdict')?.textContent || 'N/A';
                
                resultsText = `
INBOXQUALIFY ANALYSIS REPORT
Generated: ${new Date().toLocaleString()}

EMAIL SUBJECT: ${subjectValue}

EMAIL BODY:
${bodyValue}

ANALYSIS RESULTS:
Overall Score: ${score}
Verdict: ${verdict}

DETAILED FEEDBACK:
${Array.from(resultsCard.querySelectorAll('.category-score')).map(cat => {
    const title = cat.querySelector('.category-title')?.textContent || '';
    const feedback = cat.querySelector('.category-feedback')?.textContent || '';
    return `${title}\n${feedback}\n`;
}).join('\n')}

---
Powered by InboxQualify - AI Email Analysis
                `.trim();
            }
        } catch (error) {
            resultsText = 'Unable to copy results. Please try again.';
        }
        
        navigator.clipboard.writeText(resultsText).then(() => {
            const btn = document.getElementById('copy-results');
            const originalText = btn.textContent;
            btn.textContent = '✅ Copied!';
            btn.style.background = 'var(--success)';
            btn.style.color = 'white';
            
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '';
                btn.style.color = '';
            }, 2000);
        }).catch(() => {
            alert('Unable to copy to clipboard. Please manually select and copy the text.');
        });
    }
});