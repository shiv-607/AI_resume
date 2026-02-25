// Resume plagiarism checker functionality
document.addEventListener('DOMContentLoaded', function() {
    const plagiarismForm = document.getElementById('plagiarismForm');
    const loadingSpinner = document.getElementById('plagiarismLoadingSpinner');
    const plagiarismResults = document.getElementById('plagiarismResults');

    if (plagiarismForm) {
        plagiarismForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Show loading spinner
            loadingSpinner.style.display = 'block';
            plagiarismResults.style.display = 'none';

            const formData = new FormData(plagiarismForm);

            fetch('/check-plagiarism', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading spinner
                loadingSpinner.style.display = 'none';

                if (data.success) {
                    displayPlagiarismResults(data.results);
                    plagiarismResults.style.display = 'block';
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                loadingSpinner.style.display = 'none';
                alert('An error occurred while checking plagiarism.');
                console.error('Error:', error);
            });
        });
    }

    function displayPlagiarismResults(results) {
        // Set plagiarism score
        const scoreElement = document.getElementById('plagiarismScoreCircle');
        scoreElement.textContent = results.score + '%';
        scoreElement.className = 'score-circle';
        if (results.score < 20) {
            scoreElement.classList.add('bg-success');
        } else if (results.score < 50) {
            scoreElement.classList.add('bg-warning');
        } else {
            scoreElement.classList.add('bg-danger');
        }

        // Set assessment
        document.getElementById('plagiarismAssessment').textContent = results.assessment;

        // Populate sections
        const sectionsContainer = document.getElementById('plagiarizedSections');
        sectionsContainer.innerHTML = '';

        results.sections.forEach(section => {
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'list-group-item list-group-item-action flex-column align-items-start';

            const headerDiv = document.createElement('div');
            headerDiv.className = 'd-flex w-100 justify-content-between';

            const heading = document.createElement('h6');
            heading.className = 'mb-1';
            heading.textContent = `Similarity: ${section.similarity}%`;

            headerDiv.appendChild(heading);
            sectionDiv.appendChild(headerDiv);

            const textPara = document.createElement('p');
            textPara.className = 'mb-1';
            textPara.textContent = section.text;
            sectionDiv.appendChild(textPara);

            const sourceSmall = document.createElement('small');
            sourceSmall.className = 'text-muted';
            sourceSmall.textContent = `Possible source: ${section.source || 'Unknown'}`;
            sectionDiv.appendChild(sourceSmall);

            sectionsContainer.appendChild(sectionDiv);
        });

        // Populate recommendations
        const recommendationsList = document.getElementById('plagiarismRecommendations');
        recommendationsList.innerHTML = '';

        results.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = rec;
            recommendationsList.appendChild(li);
        });
    }
});