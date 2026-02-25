// Resume comparison functionality 
document.addEventListener('DOMContentLoaded', function() { 
    const compareForm = document.getElementById('compareForm'); 
    const loadingSpinner = document.getElementById('loadingSpinner'); 
    const comparisonResults = document.getElementById('comparisonResults'); 
 
    if (compareForm) { 
        compareForm.addEventListener('submit', function(e) { 
            e.preventDefault(); 
 
            // Show loading spinner 
            loadingSpinner.style.display = 'block'; 
            comparisonResults.style.display = 'none'; 
 
            const formData = new FormData(compareForm); 
 
            fetch('/compare', { 
                method: 'POST', 
                body: formData 
            }) 
            .then(response => response.json()) 
            .then(data => { 
                // Hide loading spinner 
                loadingSpinner.style.display = 'none'; 
 
                if (data.success) { 
                    displayComparisonResults(data.comparison); 
                    comparisonResults.style.display = 'block'; 
                } else { 
                    alert('Error: ' + data.error); 
                } 
            }) 
            .catch(error => { 
                loadingSpinner.style.display = 'none'; 
                alert('An error occurred while comparing resumes.'); 
                console.error('Error:', error); 
            }); 
        }); 
    } 
 
    function displayComparisonResults(comparison) { 
        // Set scores 
        document.getElementById('score1Circle').textContent = comparison.overall_comparison.score_resume1; 
        document.getElementById('score2Circle').textContent = comparison.overall_comparison.score_resume2; 
 
        // Set winner badge 
        const winnerBadge = document.getElementById('winnerBadge'); 
        if (comparison.overall_comparison.stronger_resume === "1") { 
            winnerBadge.style.display = 'block'; 
            winnerBadge.parentElement.parentElement.classList.remove('col-md-6'); 
            winnerBadge.parentElement.parentElement.previousElementSibling.classList.add('col-md-6'); 
            winnerBadge.parentElement.parentElement.previousElementSibling.querySelector('.comparison-card').appendChild(winnerBadge); 
        } else if (comparison.overall_comparison.stronger_resume === "2") { 
            winnerBadge.style.display = 'block'; 
        } else { 
            winnerBadge.style.display = 'none'; 
        } 
 
        // Populate differences 
        populateDifferences('experienceDifferences', comparison.key_differences.experience); 
        populateDifferences('skillsDifferences', comparison.key_differences.skills); 
        populateDifferences('educationDifferences', comparison.key_differences.education); 
 
        // Populate recommendations 
        populateList('strengths1List', comparison.recommendations.resume1); 
        populateList('improvements1List', comparison.recommendations.resume1); 
        populateList('strengths2List', comparison.recommendations.resume2); 
        populateList('improvements2List', comparison.recommendations.resume2); 
    } 
 
    function populateDifferences(elementId, items) { 
        const container = document.getElementById(elementId); 
        container.innerHTML = ''; 
 
        items.forEach(item => { 
            const div = document.createElement('div'); 
            div.className = 'difference-item'; 
            div.textContent = item; 
            container.appendChild(div); 
        }); 
    } 
 
    function populateList(elementId, items) { 
        const list = document.getElementById(elementId); 
        list.innerHTML = ''; 
 
        items.forEach(item => { 
            const li = document.createElement('li'); 
            li.className = 'list-group-item'; 
            li.textContent = item; 
            list.appendChild(li); 
        }); 
    } 
}); 
