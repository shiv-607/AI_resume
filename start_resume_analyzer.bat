@echo off
echo ===================================
echo    Resume Analyzer - Startup Tool
echo ===================================
echo.

:: Change to the correct directory
cd /d "C:\Users\tiwar\OneDrive\Desktop\New folder (2)"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python and try again.
    goto :error
)

:: Check if required packages are installed
echo Checking required packages...
python -c "import flask, openai, PyPDF2, docx" >nul 2>&1
if %errorlevel% neq 0 (
    echo Some required packages are missing. Installing now...
    pip install flask openai python-docx PyPDF2
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install required packages.
        goto :error
    )
    echo Packages installed successfully.
)

:: Create uploads directory if it doesn't exist
if not exist "static\uploads" mkdir "static\uploads"

:: Create examples directory if it doesn't exist
if not exist "static\examples" mkdir "static\examples"

:: Check if static/js directory exists and create it if not
if not exist "static\js" mkdir "static\js"

:: Create or update the compare.js file for the compare functionality
echo Creating/updating JavaScript files...
echo // Resume comparison functionality > "static\js\compare.js"
echo document.addEventListener('DOMContentLoaded', function() { >> "static\js\compare.js"
echo     const compareForm = document.getElementById('compareForm'); >> "static\js\compare.js"
echo     const loadingSpinner = document.getElementById('loadingSpinner'); >> "static\js\compare.js"
echo     const comparisonResults = document.getElementById('comparisonResults'); >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo     if (compareForm) { >> "static\js\compare.js"
echo         compareForm.addEventListener('submit', function(e) { >> "static\js\compare.js"
echo             e.preventDefault(); >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo             // Show loading spinner >> "static\js\compare.js"
echo             loadingSpinner.style.display = 'block'; >> "static\js\compare.js"
echo             comparisonResults.style.display = 'none'; >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo             const formData = new FormData(compareForm); >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo             fetch('/compare', { >> "static\js\compare.js"
echo                 method: 'POST', >> "static\js\compare.js"
echo                 body: formData >> "static\js\compare.js"
echo             }) >> "static\js\compare.js"
echo             .then(response =^> response.json()) >> "static\js\compare.js"
echo             .then(data =^> { >> "static\js\compare.js"
echo                 // Hide loading spinner >> "static\js\compare.js"
echo                 loadingSpinner.style.display = 'none'; >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo                 if (data.success) { >> "static\js\compare.js"
echo                     displayComparisonResults(data.comparison); >> "static\js\compare.js"
echo                     comparisonResults.style.display = 'block'; >> "static\js\compare.js"
echo                 } else { >> "static\js\compare.js"
echo                     alert('Error: ' + data.error); >> "static\js\compare.js"
echo                 } >> "static\js\compare.js"
echo             }) >> "static\js\compare.js"
echo             .catch(error =^> { >> "static\js\compare.js"
echo                 loadingSpinner.style.display = 'none'; >> "static\js\compare.js"
echo                 alert('An error occurred while comparing resumes.'); >> "static\js\compare.js"
echo                 console.error('Error:', error); >> "static\js\compare.js"
echo             }); >> "static\js\compare.js"
echo         }); >> "static\js\compare.js"
echo     } >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo     function displayComparisonResults(comparison) { >> "static\js\compare.js"
echo         // Set scores >> "static\js\compare.js"
echo         document.getElementById('score1Circle').textContent = comparison.overall_comparison.score_resume1; >> "static\js\compare.js"
echo         document.getElementById('score2Circle').textContent = comparison.overall_comparison.score_resume2; >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo         // Set winner badge >> "static\js\compare.js"
echo         const winnerBadge = document.getElementById('winnerBadge'); >> "static\js\compare.js"
echo         if (comparison.overall_comparison.stronger_resume === "1") { >> "static\js\compare.js"
echo             winnerBadge.style.display = 'block'; >> "static\js\compare.js"
echo             winnerBadge.parentElement.parentElement.classList.remove('col-md-6'); >> "static\js\compare.js"
echo             winnerBadge.parentElement.parentElement.previousElementSibling.classList.add('col-md-6'); >> "static\js\compare.js"
echo             winnerBadge.parentElement.parentElement.previousElementSibling.querySelector('.comparison-card').appendChild(winnerBadge); >> "static\js\compare.js"
echo         } else if (comparison.overall_comparison.stronger_resume === "2") { >> "static\js\compare.js"
echo             winnerBadge.style.display = 'block'; >> "static\js\compare.js"
echo         } else { >> "static\js\compare.js"
echo             winnerBadge.style.display = 'none'; >> "static\js\compare.js"
echo         } >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo         // Populate differences >> "static\js\compare.js"
echo         populateDifferences('experienceDifferences', comparison.key_differences.experience); >> "static\js\compare.js"
echo         populateDifferences('skillsDifferences', comparison.key_differences.skills); >> "static\js\compare.js"
echo         populateDifferences('educationDifferences', comparison.key_differences.education); >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo         // Populate recommendations >> "static\js\compare.js"
echo         populateList('strengths1List', comparison.recommendations.resume1); >> "static\js\compare.js"
echo         populateList('improvements1List', comparison.recommendations.resume1); >> "static\js\compare.js"
echo         populateList('strengths2List', comparison.recommendations.resume2); >> "static\js\compare.js"
echo         populateList('improvements2List', comparison.recommendations.resume2); >> "static\js\compare.js"
echo     } >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo     function populateDifferences(elementId, items) { >> "static\js\compare.js"
echo         const container = document.getElementById(elementId); >> "static\js\compare.js"
echo         container.innerHTML = ''; >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo         items.forEach(item =^> { >> "static\js\compare.js"
echo             const div = document.createElement('div'); >> "static\js\compare.js"
echo             div.className = 'difference-item'; >> "static\js\compare.js"
echo             div.textContent = item; >> "static\js\compare.js"
echo             container.appendChild(div); >> "static\js\compare.js"
echo         }); >> "static\js\compare.js"
echo     } >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo     function populateList(elementId, items) { >> "static\js\compare.js"
echo         const list = document.getElementById(elementId); >> "static\js\compare.js"
echo         list.innerHTML = ''; >> "static\js\compare.js"
echo. >> "static\js\compare.js"
echo         items.forEach(item =^> { >> "static\js\compare.js"
echo             const li = document.createElement('li'); >> "static\js\compare.js"
echo             li.className = 'list-group-item'; >> "static\js\compare.js"
echo             li.textContent = item; >> "static\js\compare.js"
echo             list.appendChild(li); >> "static\js\compare.js"
echo         }); >> "static\js\compare.js"
echo     } >> "static\js\compare.js"
echo }); >> "static\js\compare.js"

echo.
echo Starting Resume Analyzer application...
echo.
echo Access the application at: http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo ===================================
echo.

:: Start the Flask application
python app.py

if %errorlevel% neq 0 (
    echo ERROR: The application encountered an error.
    goto :error
)

goto :end

:error
echo.
echo Application failed to start properly.
echo.

:end
pause