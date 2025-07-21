// Property Risk Analyzer JavaScript

let currentAnalysisData = null;

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const progressBar = document.getElementById('progressBar');
const infoAlert = document.getElementById('infoAlert');
const infoMessage = document.getElementById('infoMessage');
const resultsContent = document.getElementById('resultsContent');
const exportBtn = document.getElementById('exportBtn');
const thinkingTraces = document.getElementById('thinkingTraces');
const thinkingContent = document.getElementById('thinkingContent');
const showThinkingBtn = document.getElementById('showThinkingBtn');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    setupFileInput();
});

// Setup drag and drop functionality
function setupDragAndDrop() {
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
}

// Setup file input
function setupFileInput() {
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
}

// Handle file upload
function handleFile(file) {
    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain'];
    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
        showInfo('Please select a PDF or text file.', 'danger');
        return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
        showInfo('File size must be less than 10MB.', 'danger');
        return;
    }

    uploadFile(file);
}

// Upload file to server
function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    // Show progress and thinking traces
    showProgress();
    showThinkingTraces();
    showInfo('Starting analysis...', 'info');

    console.log('Uploading file:', file.name);

    // Use streaming endpoint for real-time analysis
    fetch('/stream-analysis', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        function processStream() {
            return reader.read().then(({ done, value }) => {
                if (done) {
                    return;
                }
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            console.log('Stream data:', data);
                            handleStreamData(data);
                        } catch (e) {
                            console.error('Error parsing stream data:', e);
                        }
                    }
                }
                
                return processStream();
            });
        }
        
        return processStream();
    })
    .catch(error => {
        console.error('Upload error:', error);
        hideProgress();
        hideThinkingTraces();
        showInfo('Error uploading file: ' + error.message, 'danger');
    });
}

// Handle streaming data
function handleStreamData(data) {
    switch(data.type) {
        case 'status':
            showInfo(data.message, 'info');
            updateThinkingContent(`<div class="text-info"><i class="fas fa-info-circle me-2"></i>${data.message}</div>`);
            break;

        case 'thinking_start':
            updateThinkingContent(`
                <div class="text-primary mb-3">
                    <i class="fas fa-brain me-2"></i>
                    <strong>AI Analysis Started</strong>
                </div>
                <div class="thinking-sections"></div>
            `);
            break;

        case 'thinking_section':
            addThinkingSection(data.section, data.message);
            break;

        case 'thinking_result':
            updateThinkingSection(data.section, data.trace);
            break;

        case 'complete':
            hideProgress();
            hideThinkingTraces();
            currentAnalysisData = data.data;
            displayResults(data.data);
            showInfo('Analysis completed successfully!', 'success');
            break;

        case 'error':
            hideProgress();
            hideThinkingTraces();
            showInfo('Error: ' + data.message, 'danger');
            break;
    }
}

// Display analysis results
function displayResults(data) {
    console.log('Displaying results:', data);
    
    // Check if data has the expected structure
    if (!data) {
        console.error('No data received');
        showInfo('No data received from server', 'danger');
        return;
    }
    
    if (data.error) {
        console.error('Error in data:', data.error);
        showInfo(data.error, 'danger');
        return;
    }
    
    const resultsHtml = `
        <div class="fade-in-up">
            <!-- Summary Section -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="summary-card">
                        <h3>${data.overall_risk_score || 'Unknown'}</h3>
                        <p>Overall Risk Score</p>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="summary-card">
                        <h3>${data.risk_factors ? data.risk_factors.length : 0}</h3>
                        <p>Risk Factors Found</p>
                    </div>
                </div>
            </div>

            <!-- Summary Text -->
            ${data.summary ? `
                <div class="alert alert-info mb-4">
                    <h6><i class="fas fa-info-circle me-2"></i>Analysis Summary</h6>
                    <p class="mb-0">${data.summary}</p>
                </div>
            ` : ''}

            <!-- Risk Factors -->
            ${data.risk_factors && data.risk_factors.length > 0 ? `
                <h5 class="mb-3">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Identified Risk Factors (${data.risk_factors.length})
                </h5>
                <div class="row">
                    ${data.risk_factors.map((risk, index) => createRiskCard(risk, index)).join('')}
                </div>
            ` : `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    No significant risk factors identified in this report.
                </div>
            `}

            <!-- File Information -->
            <div class="mt-4 p-3 bg-light rounded">
                <small class="text-muted">
                    <i class="fas fa-file me-1"></i>
                    File: ${data.filename || 'Unknown'} | 
                    <i class="fas fa-clock me-1"></i>
                    Analyzed: ${new Date(data.upload_time).toLocaleString()}
                </small>
            </div>
        </div>
    `;

    console.log('Generated HTML:', resultsHtml);
    resultsContent.innerHTML = resultsHtml;
    exportBtn.classList.remove('d-none');
    
    // Show thinking traces button if available
    if (data.thinking_traces && data.thinking_traces.length > 0) {
        showThinkingBtn.classList.remove('d-none');
    }
    
    console.log('Results displayed successfully');
}

// Create risk factor card
function createRiskCard(risk, index) {
    const severityClass = getSeverityClass(risk.severity);
    const categoryIcon = getCategoryIcon(risk.category);
    
    return `
        <div class="col-lg-6 mb-3">
            <div class="card risk-card ${risk.severity.toLowerCase()}" onclick="showRiskDetails(${index})">
                <div class="card-body">
                    <div class="d-flex align-items-start">
                        <div class="risk-category-icon ${getCategoryClass(risk.category)}">
                            <i class="${categoryIcon}"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="mb-0">${risk.category || 'Unknown Category'}</h6>
                                <span class="badge ${severityClass}">${risk.severity || 'Unknown'}</span>
                            </div>
                            <p class="small text-muted mb-2">${risk.description || 'No description available'}</p>
                            ${risk.location ? `<small class="text-muted"><i class="fas fa-map-marker-alt me-1"></i>${risk.location}</small>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Get severity class for styling
function getSeverityClass(severity) {
    switch(severity?.toLowerCase()) {
        case 'critical': return 'badge-critical';
        case 'high': return 'badge-high';
        case 'medium': return 'badge-medium';
        case 'low': return 'badge-low';
        default: return 'badge-secondary';
    }
}

// Get category icon
function getCategoryIcon(category) {
    const icons = {
        'Structural Issues': 'fas fa-building',
        'Electrical Hazards': 'fas fa-bolt',
        'Plumbing Problems': 'fas fa-tint',
        'Roofing Issues': 'fas fa-home',
        'HVAC Concerns': 'fas fa-snowflake',
        'Safety Violations': 'fas fa-exclamation-triangle',
        'Environmental Hazards': 'fas fa-leaf',
        'Accessibility Issues': 'fas fa-wheelchair',
        'Property Condition': 'fas fa-tools'
    };
    return icons[category] || 'fas fa-exclamation-circle';
}

// Get category class for styling
function getCategoryClass(category) {
    const classes = {
        'Structural Issues': 'structural',
        'Electrical Hazards': 'electrical',
        'Plumbing Problems': 'plumbing',
        'Roofing Issues': 'roofing',
        'HVAC Concerns': 'hvac',
        'Safety Violations': 'safety',
        'Environmental Hazards': 'environmental',
        'Accessibility Issues': 'accessibility',
        'Property Condition': 'condition'
    };
    return classes[category] || 'condition';
}

// Show risk factor details in modal
function showRiskDetails(index) {
    if (!currentAnalysisData || !currentAnalysisData.risk_factors) return;
    
    const risk = currentAnalysisData.risk_factors[index];
    const modalBody = document.getElementById('riskModalBody');
    
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Category</h6>
                <p>${risk.category || 'Unknown'}</p>
                
                <h6>Severity</h6>
                <span class="badge ${getSeverityClass(risk.severity)}">${risk.severity || 'Unknown'}</span>
                
                ${risk.location ? `
                    <h6 class="mt-3">Location</h6>
                    <p>${risk.location}</p>
                ` : ''}
            </div>
            <div class="col-md-6">
                <h6>Description</h6>
                <p>${risk.description || 'No description available'}</p>
                
                ${risk.recommendation ? `
                    <h6 class="mt-3">Recommendation</h6>
                    <p>${risk.recommendation}</p>
                ` : ''}
                
                ${risk.cost_impact ? `
                    <h6 class="mt-3">Cost Impact</h6>
                    <p>${risk.cost_impact}</p>
                ` : ''}
            </div>
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('riskModal'));
    modal.show();
}

// Export report
function exportReport() {
    if (!currentAnalysisData) return;
    
    fetch('/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentAnalysisData)
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `risk_analysis_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        showInfo('Error exporting report: ' + error.message, 'danger');
    });
}

// Show progress bar
function showProgress() {
    progressBar.classList.remove('d-none');
    progressBar.querySelector('.progress-bar').style.width = '0%';
    
    // Animate progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        progressBar.querySelector('.progress-bar').style.width = progress + '%';
    }, 500);
    
    // Store interval for cleanup
    progressBar.dataset.interval = interval;
}

// Hide progress bar
function hideProgress() {
    progressBar.classList.add('d-none');
    if (progressBar.dataset.interval) {
        clearInterval(parseInt(progressBar.dataset.interval));
    }
    progressBar.querySelector('.progress-bar').style.width = '100%';
}

// Show thinking traces
function showThinkingTraces() {
    thinkingTraces.classList.remove('d-none');
    thinkingContent.classList.remove('d-none');
}

// Hide thinking traces
function hideThinkingTraces() {
    thinkingTraces.classList.add('d-none');
    thinkingContent.classList.add('d-none');
}

// Toggle thinking traces modal
function toggleThinkingTraces() {
    if (!currentAnalysisData || !currentAnalysisData.thinking_traces) return;
    
    const modalBody = document.getElementById('thinkingModalBody');
    const traces = currentAnalysisData.thinking_traces;
    
    let tracesHtml = `
        <div class="mb-4">
            <h6 class="text-muted">AI Analysis Process</h6>
            <p class="small text-muted">This shows how the AI analyzed each section of the inspection report.</p>
        </div>
    `;
    
    traces.forEach((trace, index) => {
        tracesHtml += `
            <div class="card mb-3">
                <div class="card-header bg-light">
                    <h6 class="mb-0">
                        <i class="fas fa-search me-2"></i>
                        ${trace.section || 'Section ' + (index + 1)}
                    </h6>
                </div>
                <div class="card-body">
                    ${trace.issues_found && trace.issues_found.length > 0 ? `
                        <div class="mb-3">
                            <strong>Issues Identified:</strong>
                            <ul class="mb-0">
                                ${trace.issues_found.map(issue => `<li>${issue}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${trace.reasoning ? `
                        <div class="mb-3">
                            <strong>Reasoning:</strong>
                            <p class="mb-0">${trace.reasoning}</p>
                        </div>
                    ` : ''}
                    
                    ${trace.evidence ? `
                        <div class="mb-3">
                            <strong>Evidence:</strong>
                            <p class="mb-0">${trace.evidence}</p>
                        </div>
                    ` : ''}
                    
                    ${trace.severity_assessment ? `
                        <div>
                            <strong>Severity Assessment:</strong>
                            <p class="mb-0">${trace.severity_assessment}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    modalBody.innerHTML = tracesHtml;
    
    const modal = new bootstrap.Modal(document.getElementById('thinkingModal'));
    modal.show();
}

// Show info message
function showInfo(message, type = 'info') {
    infoMessage.textContent = message;
    infoAlert.className = `alert alert-${type} mt-3`;
    infoAlert.classList.remove('d-none');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        infoAlert.classList.add('d-none');
    }, 5000);
} 

// Update thinking content
function updateThinkingContent(content) {
    thinkingContent.innerHTML = content;
}

// Add a new thinking section
function addThinkingSection(section, message) {
    const sectionsContainer = thinkingContent.querySelector('.thinking-sections');
    if (sectionsContainer) {
        const sectionHtml = `
            <div class="thinking-section mb-3" data-section="${section}">
                <div class="card">
                    <div class="card-header bg-light">
                        <h6 class="mb-0">
                            <i class="fas fa-search me-2"></i>
                            ${section}
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="thinking-status">
                            <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                            <span>${message}</span>
                        </div>
                        <div class="thinking-result d-none"></div>
                    </div>
                </div>
            </div>
        `;
        sectionsContainer.insertAdjacentHTML('beforeend', sectionHtml);
    }
}

// Update thinking section with results
function updateThinkingSection(section, trace) {
    const sectionElement = thinkingContent.querySelector(`[data-section="${section}"]`);
    if (sectionElement) {
        const statusElement = sectionElement.querySelector('.thinking-status');
        const resultElement = sectionElement.querySelector('.thinking-result');
        
        // Update status
        statusElement.innerHTML = `
            <div class="text-success">
                <i class="fas fa-check-circle me-2"></i>
                Analysis complete
            </div>
        `;
        
        // Show results
        resultElement.classList.remove('d-none');
        resultElement.innerHTML = `
            ${trace.issues_found && trace.issues_found.length > 0 ? `
                <div class="mb-2">
                    <strong>Issues Found:</strong>
                    <ul class="mb-0 small">
                        ${trace.issues_found.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${trace.reasoning ? `
                <div class="mb-2">
                    <strong>Reasoning:</strong>
                    <p class="mb-0 small">${trace.reasoning}</p>
                </div>
            ` : ''}
            
            ${trace.evidence ? `
                <div class="mb-2">
                    <strong>Evidence:</strong>
                    <p class="mb-0 small">${trace.evidence}</p>
                </div>
            ` : ''}
            
            ${trace.severity_assessment ? `
                <div>
                    <strong>Severity:</strong>
                    <p class="mb-0 small">${trace.severity_assessment}</p>
                </div>
            ` : ''}
        `;
        
        // Add animation
        sectionElement.style.animation = 'fadeInUp 0.5s ease-out';
    }
} 