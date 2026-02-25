document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const resumeForm = document.getElementById('resume-form');
    const resumeFile = document.getElementById('resume-file');
    const dropArea = document.getElementById('drop-area');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const removeFile = document.getElementById('remove-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    const uploadSection = document.getElementById('upload-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const backBtn = document.getElementById('back-btn');
    const scoreBar = document.getElementById('score-bar');
    const strengthsList = document.getElementById('strengths-list');
    const improvementsList = document.getElementById('improvements-list');
    const keywordsDetected = document.getElementById('keywords-detected');
    const keywordsMissing = document.getElementById('keywords-missing');

    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            handleFiles(files[0]);
        }
    }

    // File selection handling
    resumeFile.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFiles(this.files[0]);
        }
    });

    function handleFiles(file) {
        // Check file type
        const fileType = file.name.split('.').pop().toLowerCase();
        const allowedTypes = ['pdf', 'docx', 'txt'];
        
        if (!allowedTypes.includes(fileType)) {
            alert('Please upload a PDF, DOCX, or TXT file.');
            return;
        }
        
        // Check file size (max 16MB)
        if (file.size > 16 * 1024 * 1024) {
            alert('File size exceeds 16MB limit.');
            return;
        }
        
        // Display file info
        fileName.textContent = file.name;
        fileInfo.classList.remove('d-none');
        analyzeBtn.disabled = false;
        
        // Store file in form data
        resumeForm.file = file;
    }

    // Remove file button
    removeFile.addEventListener('click', function() {
        resumeFile.value = '';
        fileInfo.classList.add('d-none');
        analyzeBtn.disabled = true;
        resumeForm.file = null;
    });

    // Form submission
    resumeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!resumeForm.file) {
            alert('Please select a resume file.');
            return;
        }
        
        // Show loading section
        uploadSection.classList.add('d-none');
        loadingSection.classList.remove('d-none');
        
        // Create form data
        const formData = new FormData();
        formData.append('resume', resumeForm.file);
        
        // Send request to server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                displayResults(data.analysis);
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            alert('Error: ' + error.message);
            // Go back to upload section
            loadingSection.classList.add('d-none');
            uploadSection.classList.remove('d-none');
        });
    });

    // Display analysis results
    function displayResults(analysis) {
        // Hide loading section
        loadingSection.classList.add('d-none');
        resultsSection.classList.remove('d-none');
        
        // Update score
        const score = analysis.score;
        scoreBar.style.width = score + '%';
        scoreBar.textContent = score + '%';
        scoreBar.setAttribute('aria-valuenow', score);
        
        // Set score color based on value
        if (score < 50) {
            scoreBar.classList.remove('bg-success', 'bg-warning');
            scoreBar.classList.add('bg-danger');
        } else if (score < 75) {
            scoreBar.classList.remove('bg-success', 'bg-danger');
            scoreBar.classList.add('bg-warning');
        } else {
            scoreBar.classList.remove('bg-warning', 'bg-danger');
            scoreBar.classList.add('bg-success');
        }
        
        // Update strengths
        strengthsList.innerHTML = '';
        analysis.feedback.strengths.forEach(strength => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.innerHTML = `<i class="fas fa-check-circle text-success me-2"></i>${strength}`;
            strengthsList.appendChild(li);
        });
        
        // Update improvements
        improvementsList.innerHTML = '';
        analysis.feedback.improvements.forEach(improvement => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.innerHTML = `<i class="fas fa-exclamation-circle text-warning me-2"></i>${improvement}`;
            improvementsList.appendChild(li);
        });
        
        // Update keywords
        keywordsDetected.innerHTML = '';
        analysis.keywords_detected.forEach(keyword => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-success me-2 mb-2';
            badge.textContent = keyword;
            keywordsDetected.appendChild(badge);
        });
        
        keywordsMissing.innerHTML = '';
        analysis.missing_keywords.forEach(keyword => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-secondary me-2 mb-2';
            badge.textContent = keyword;
            keywordsMissing.appendChild(badge);
        });
        
        // Add suggested improvements section
        if (analysis.suggested_improvements) {
            const suggestedImprovementsSection = document.getElementById('suggested-improvements-section');
            const suggestedImprovementsList = document.getElementById('suggested-improvements-list');
            
            suggestedImprovementsList.innerHTML = '';
            
            // Create a table for side-by-side comparison
            const table = document.createElement('table');
            table.className = 'table table-bordered';
            
            // Add table header
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th class="bg-light">Original Line</th>
                    <th class="bg-light">Suggested Improvement</th>
                </tr>
            `;
            table.appendChild(thead);
            
            // Add table body
            const tbody = document.createElement('tbody');
            
            for (let i = 0; i < analysis.suggested_improvements.original_lines.length; i++) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="text-danger">${analysis.suggested_improvements.original_lines[i]}</td>
                    <td class="text-success">${analysis.suggested_improvements.suggested_lines[i]}</td>
                `;
                tbody.appendChild(tr);
            }
            
            table.appendChild(tbody);
            suggestedImprovementsList.appendChild(table);
            suggestedImprovementsSection.classList.remove('d-none');
        }
    }

    // Back button
    backBtn.addEventListener('click', function() {
        // Reset form
        resumeFile.value = '';
        fileInfo.classList.add('d-none');
        analyzeBtn.disabled = true;
        resumeForm.file = null;
        
        // Hide results section
        resultsSection.classList.add('d-none');
        
        // Show upload section
        uploadSection.classList.remove('d-none');
    });

    // Click on drop area to trigger file input
    dropArea.addEventListener('click', function() {
        resumeFile.click();
    });
});

// Add this to your existing main.js file

// Download report functionality
const downloadReportBtn = document.getElementById('download-report');

downloadReportBtn.addEventListener('click', function() {
    // Get the analysis data
    const score = scoreBar.textContent;
    
    // Create strengths list
    let strengthsText = '';
    document.querySelectorAll('#strengths-list li').forEach(item => {
        strengthsText += '- ' + item.textContent.trim() + '\n';
    });
    
    // Create improvements list
    let improvementsText = '';
    document.querySelectorAll('#improvements-list li').forEach(item => {
        improvementsText += '- ' + item.textContent.trim() + '\n';
    });
    
    // Create keywords lists
    let keywordsDetectedText = '';
    document.querySelectorAll('#keywords-detected .badge').forEach(badge => {
        keywordsDetectedText += badge.textContent.trim() + ', ';
    });
    keywordsDetectedText = keywordsDetectedText.slice(0, -2); // Remove last comma
    
    let keywordsMissingText = '';
    document.querySelectorAll('#keywords-missing .badge').forEach(badge => {
        keywordsMissingText += badge.textContent.trim() + ', ';
    });
    keywordsMissingText = keywordsMissingText.slice(0, -2); // Remove last comma
    
    // Create suggested improvements text
    let suggestedImprovementsText = '';
    if (!document.getElementById('suggested-improvements-section').classList.contains('d-none')) {
        document.querySelectorAll('#suggested-improvements-list tbody tr').forEach(row => {
            const original = row.cells[0].textContent.trim();
            const suggested = row.cells[1].textContent.trim();
            suggestedImprovementsText += 'Original: ' + original + '\nSuggested: ' + suggested + '\n\n';
        });
    }
    
    // Create the report content
    const reportContent = `
RESUME ANALYSIS REPORT
=====================

Overall Score: ${score}

STRENGTHS:
${strengthsText}

AREAS FOR IMPROVEMENT:
${improvementsText}

KEYWORDS DETECTED:
${keywordsDetectedText}

SUGGESTED KEYWORDS:
${keywordsMissingText}

${suggestedImprovementsText ? 'SUGGESTED LINE IMPROVEMENTS:\n' + suggestedImprovementsText : ''}

Report generated on ${new Date().toLocaleString()}
    `;
    
    // Create a blob and download link
    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'resume_analysis_report.txt';
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
});