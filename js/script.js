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
            
            <!-- AI Rewrite and Suggestions Section -->
            <div class="ai-actions" style="margin-top: 2rem; padding-top: 2rem; border-top: 1px solid var(--gray-200);">
                <h3 style="color: var(--gray-700); margin-bottom: 1rem; font-size: 1.1rem;">🚀 Improve Your Email</h3>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    <button type="button" id="get-suggestions" class="secondary-button" style="flex: 1; min-width: 150px;">
                        💡 Get Suggestions
                    </button>
                    <button type="button" id="ai-rewrite" class="cta-button" style="flex: 1; min-width: 150px;">
                        ✨ AI Rewrite
                    </button>
                </div>
            </div>
        `;
        
        resultsContainer.appendChild(card);
        
        // Show export section
        document.getElementById('export-section').style.display = 'block';
        
        // Store current email data for AI features
        window.currentEmailData = {
            subject: document.getElementById('subject').value,
            body: document.getElementById('email-body').value,
            analysis: data
        };
        
        // Initialize AI feature buttons
        initializeAIFeatures();
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
    
    // === AI FEATURES IMPLEMENTATION ===
    
    function initializeAIFeatures() {
        // Get Suggestions Button
        const getSuggestionsBtn = document.getElementById('get-suggestions');
        if (getSuggestionsBtn) {
            getSuggestionsBtn.addEventListener('click', handleGetSuggestions);
        }
        
        // AI Rewrite Button
        const aiRewriteBtn = document.getElementById('ai-rewrite');
        if (aiRewriteBtn) {
            aiRewriteBtn.addEventListener('click', handleAIRewrite);
        }
    }
    
    async function handleGetSuggestions() {
        if (!window.currentEmailData) {
            showError('No email data available');
            return;
        }
        
        try {
            const response = await fetch(API_CONFIG.getURL('/suggestions'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    subject: window.currentEmailData.subject,
                    body: window.currentEmailData.body
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showSuggestions(data.data);
            } else {
                showError('Failed to get suggestions');
            }
        } catch (error) {
            showError('Error getting suggestions: ' + error.message);
        }
    }
    
    async function handleAIRewrite() {
        if (!window.currentEmailData) {
            showError('No email data available');
            return;
        }
        
        // Show AI rewrite section
        document.getElementById('ai-rewrite-section').style.display = 'block';
        
        // Scroll to the rewrite section
        document.getElementById('ai-rewrite-section').scrollIntoView({ 
            behavior: 'smooth' 
        });
        
        // Initialize rewrite button
        const performRewriteBtn = document.getElementById('perform-rewrite');
        if (performRewriteBtn) {
            performRewriteBtn.onclick = performRewrite;
        }
    }
    
    async function performRewrite() {
        if (!window.currentEmailData) {
            showError('No email data available');
            return;
        }
        
        // Collect context
        const context = {
            company: document.getElementById('company-name').value || undefined,
            name: document.getElementById('recipient-name').value || undefined,
            industry: document.getElementById('industry').value || undefined,
            specific_detail: document.getElementById('specific-detail').value || undefined
        };
        
        // Remove undefined values
        Object.keys(context).forEach(key => context[key] === undefined && delete context[key]);
        
        try {
            showLoadingState('Rewriting email with AI...');
            
            const response = await fetch(API_CONFIG.getURL('/complete-rewrite'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    subject: window.currentEmailData.subject,
                    body: window.currentEmailData.body,
                    context: context
                })
            });
            
            const data = await response.json();
            
            hideLoadingState();
            
            if (data.status === 'success') {
                showRewriteResults(data.data);
            } else {
                showError('Failed to rewrite email: ' + (data.detail || 'Unknown error'));
            }
        } catch (error) {
            hideLoadingState();
            showError('Error rewriting email: ' + error.message);
        }
    }
    
    function showRewriteResults(rewriteData) {
        // Show scores
        document.getElementById('before-score').textContent = rewriteData.improvement_score.before;
        document.getElementById('after-score').textContent = rewriteData.improvement_score.after;
        document.getElementById('improvement').textContent = '+' + rewriteData.improvement_score.improvement;
        
        // Show original email
        document.getElementById('original-subject').textContent = rewriteData.rewrite_result.original.subject;
        document.getElementById('original-body').textContent = rewriteData.rewrite_result.original.body;
        
        // Show rewritten email
        document.getElementById('rewritten-subject').textContent = rewriteData.rewrite_result.rewritten.subject;
        document.getElementById('rewritten-body').textContent = rewriteData.rewrite_result.rewritten.body;
        
        // Show results section
        document.getElementById('rewrite-results').style.display = 'block';
        
        // Initialize action buttons
        initializeRewriteActions(rewriteData);
        
        // Scroll to results
        document.getElementById('rewrite-results').scrollIntoView({ 
            behavior: 'smooth' 
        });
        
        showSuccess('Email rewritten successfully! Check the before/after comparison.');
    }
    
    function initializeRewriteActions(rewriteData) {
        // Copy rewritten email
        const copyRewrittenBtn = document.getElementById('copy-rewritten');
        if (copyRewrittenBtn) {
            copyRewrittenBtn.onclick = () => {
                const emailText = `Subject: ${rewriteData.rewrite_result.rewritten.subject}\n\n${rewriteData.rewrite_result.rewritten.body}`;
                navigator.clipboard.writeText(emailText).then(() => {
                    showSuccess('Rewritten email copied to clipboard!');
                }).catch(() => {
                    showError('Failed to copy email');
                });
            };
        }
        
        // Show details
        const showDetailsBtn = document.getElementById('show-details');
        if (showDetailsBtn) {
            showDetailsBtn.onclick = () => showRewriteDetails(rewriteData);
        }
        
        // Rewrite again
        const rewriteAgainBtn = document.getElementById('rewrite-again');
        if (rewriteAgainBtn) {
            rewriteAgainBtn.onclick = () => {
                document.getElementById('rewrite-results').style.display = 'none';
                document.getElementById('rewrite-details').style.display = 'none';
                document.getElementById('ai-rewrite-section').style.display = 'block';
                
                // Clear context fields
                document.getElementById('company-name').value = '';
                document.getElementById('recipient-name').value = '';
                document.getElementById('industry').value = '';
                document.getElementById('specific-detail').value = '';
            };
        }
    }
    
    function showRewriteDetails(rewriteData) {
        const improvementsList = document.getElementById('improvements-list');
        improvementsList.innerHTML = '';
        
        // Show improvements summary
        const summary = document.createElement('div');
        summary.style.cssText = 'background: #f0f9ff; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;';
        
        const summaryTitle = document.createElement('h3');
        summaryTitle.textContent = '📈 Improvement Summary';
        summary.appendChild(summaryTitle);
        
        const summaryList = document.createElement('ul');
        
        const wordCountItem = document.createElement('li');
        const wordReduction = rewriteData.rewrite_result.improvements.word_reduction;
        const wordChange = wordReduction > 0 ? '-' : '+';
        wordCountItem.innerHTML = `<strong>Word Count:</strong> ${rewriteData.rewrite_result.original.word_count} → ${rewriteData.rewrite_result.rewritten.word_count} (${wordChange}${Math.abs(wordReduction)} words)`;
        summaryList.appendChild(wordCountItem);
        
        const subjectLengthItem = document.createElement('li');
        subjectLengthItem.innerHTML = `<strong>Subject Length:</strong> ${rewriteData.rewrite_result.original.subject_length} → ${rewriteData.rewrite_result.rewritten.subject_length} characters`;
        summaryList.appendChild(subjectLengthItem);
        
        const areasImprovedItem = document.createElement('li');
        areasImprovedItem.innerHTML = `<strong>Areas Improved:</strong> ${rewriteData.rewrite_result.improvements.areas_improved}`;
        summaryList.appendChild(areasImprovedItem);
        
        const scoreImprovementItem = document.createElement('li');
        scoreImprovementItem.innerHTML = `<strong>Score Improvement:</strong> +${rewriteData.improvement_score.improvement} points`;
        summaryList.appendChild(scoreImprovementItem);
        
        summary.appendChild(summaryList);
        improvementsList.appendChild(summary);
        
        // Show specific improvements
        rewriteData.rewrite_result.rewrite_suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'improvement-item';
            
            const areaStrong = document.createElement('h4');
            areaStrong.textContent = suggestion.area;
            item.appendChild(areaStrong);
            
            const issueP = document.createElement('p');
            issueP.innerHTML = `<strong style="color: #dc2626;">Issue:</strong> ${suggestion.issue}`;
            item.appendChild(issueP);
            
            const solutionP = document.createElement('p');
            solutionP.innerHTML = `<strong style="color: #059669;">Solution:</strong> ${suggestion.suggestion}`;
            item.appendChild(solutionP);
            
            const exampleDiv = document.createElement('div');
            exampleDiv.className = 'example';
            exampleDiv.innerHTML = `<strong style="color: #7c3aed;">Example:</strong> ${suggestion.example}`;
            item.appendChild(exampleDiv);
            
            improvementsList.appendChild(item);
        });
        
        document.getElementById('rewrite-details').style.display = 'block';
        
        // Scroll to details
        document.getElementById('rewrite-details').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }
    
    function showSuggestions(analysisData) {
        // Create suggestions modal or section
        const suggestionsHTML = `
            <div class="suggestions-modal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; display: flex; justify-content: center; align-items: center;">
                <div style="background: white; padding: 2rem; border-radius: 12px; max-width: 600px; max-height: 80vh; overflow-y: auto;">
                    <h3 style="margin-bottom: 1rem;">💡 Email Improvement Suggestions</h3>
                    <div style="margin-bottom: 1rem;">
                        <strong>Improvement Score:</strong> ${analysisData.improvement_score}
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <strong>Word Count:</strong> ${analysisData.word_count} words | 
                        <strong>Subject Length:</strong> ${analysisData.subject_length} characters
                    </div>
                    <div>
                        ${analysisData.suggestions.length === 0 ? 
                            '<div style="color: #059669; padding: 1rem; background: #ecfdf5; border-radius: 8px;">🎉 Great job! Your email looks good with no major issues.</div>' :
                            analysisData.suggestions.map(suggestion => `
                                <div style="margin-bottom: 1rem; padding: 1rem; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 0 6px 6px 0;">
                                    <strong>${suggestion.priority.toUpperCase()} Priority:</strong><br>
                                    ${suggestion.message}
                                </div>
                            `).join('')
                        }
                    </div>
                    <button onclick="this.closest('.suggestions-modal').remove()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer;">Close</button>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', suggestionsHTML);
    }
    
    function showLoadingState(message) {
        let overlay = document.getElementById('loadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 2000;
                color: white;
                font-size: 1.2rem;
            `;
            document.body.appendChild(overlay);
        }
        
        overlay.innerHTML = `
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
                <div>${message}</div>
                <div style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">This may take a few seconds...</div>
            </div>
        `;
        overlay.style.display = 'flex';
    }
    
    function hideLoadingState() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    function showError(message) {
        let banner = document.getElementById('errorBanner');
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'errorBanner';
            banner.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #fee2e2;
                border: 1px solid #fecaca;
                color: #dc2626;
                padding: 1rem;
                border-radius: 8px;
                z-index: 1000;
                max-width: 400px;
            `;
            document.body.appendChild(banner);
        }
        
        banner.textContent = message;
        banner.style.display = 'block';
        
        setTimeout(() => {
            banner.style.display = 'none';
        }, 5000);
    }
    
    function showSuccess(message) {
        let banner = document.getElementById('successBanner');
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'successBanner';
            banner.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #d1fae5;
                border: 1px solid #a7f3d0;
                color: #065f46;
                padding: 1rem;
                border-radius: 8px;
                z-index: 1000;
                max-width: 400px;
            `;
            document.body.appendChild(banner);
        }
        
        banner.textContent = message;
        banner.style.display = 'block';
        
        setTimeout(() => {
            banner.style.display = 'none';
        }, 3000);
    }
});