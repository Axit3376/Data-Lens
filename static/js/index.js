document.addEventListener('DOMContentLoaded', () => {
    // Theme Switcher for Homepage
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        if (currentTheme === 'dark') {
            themeToggle.checked = true;
        }

        themeToggle.addEventListener('change', (e) => {
            if (e.target.checked) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
        });
    }

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const targetInput = document.getElementById('target-column');
    const uploadForm = document.getElementById('upload-form');
    
    const uploadSection = document.getElementById('upload-section');
    const progressSection = document.getElementById('progress-section');
    const progressStepsContainer = document.getElementById('progress-steps');
    const progressBarFill = document.getElementById('progress-bar-fill');
    
    let selectedFile = null;

    // Drag and Drop Events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
            alert('Please select a valid CSV file.');
            return;
        }
        selectedFile = file;
        const fileInfo = dropZone.querySelector('.file-info') || document.createElement('div');
        fileInfo.className = 'file-info';
        fileInfo.innerHTML = `
            <svg class="file-icon" viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M16,11V15H13V18H11V15H8L12,11L16,11Z" />
            </svg>
            <span class="file-name">${file.name}</span>
            <span class="file-size">(${(file.size / 1024).toFixed(1)} KB)</span>
        `;
        const oldInfo = dropZone.querySelector('.file-info');
        if (oldInfo) {
            dropZone.replaceChild(fileInfo, oldInfo);
        } else {
            dropZone.appendChild(fileInfo);
        }
        dropZone.querySelector('.upload-prompt').style.display = 'none';
        document.getElementById('analyze-btn').disabled = false;
    }

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        const targetColumn = targetInput.value.trim();

        // Switch to progress screen
        uploadSection.classList.add('hidden');
        progressSection.classList.remove('hidden');

        const steps = [
            { id: 'profiling', label: 'Profiling Dataset Structure', url: '/profiling' },
            { id: 'quality', label: 'Analyzing Data Quality & Outliers', url: '/analysis' },
            { id: 'statistics', label: 'Computing Descriptive Statistics', url: '/statistics' },
            { id: 'feature_engineering', label: 'Generating Preprocessing Suggestions', url: '/feature-engineering' },
            { id: 'visualizations', label: 'Generating Analytical Plots & Charts', url: '/visualizations' }
        ];

        // Render steps
        progressStepsContainer.innerHTML = '';
        steps.forEach(step => {
            const stepEl = document.createElement('div');
            stepEl.className = 'progress-step pending';
            stepEl.id = `step-${step.id}`;
            stepEl.innerHTML = `
                <div class="step-status-icon">
                    <span class="spinner hidden"></span>
                    <span class="check hidden">✔</span>
                    <span class="bullet"></span>
                </div>
                <div class="step-label">${step.label}</div>
            `;
            progressStepsContainer.appendChild(stepEl);
        });

        // Execute step-by-step APIs
        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];
            const stepEl = document.getElementById(`step-${step.id}`);
            
            // Mark as active
            stepEl.className = 'progress-step active';
            const spinner = stepEl.querySelector('.spinner');
            const bullet = stepEl.querySelector('.bullet');
            spinner.classList.remove('hidden');
            bullet.classList.add('hidden');

            // Update Progress Bar
            const percentComplete = (i / steps.length) * 100;
            progressBarFill.style.width = `${percentComplete}%`;

            try {
                const formData = new FormData();
                formData.append('file', selectedFile);
                if (step.id === 'visualizations' && targetColumn) {
                    formData.append('target', targetColumn);
                }

                const response = await fetch(step.url, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Server returned error status ${response.status}`);
                }

                // Wait a tiny moment for smooth visual pacing
                await new Promise(resolve => setTimeout(resolve, 800));

                // Mark step completed
                stepEl.className = 'progress-step completed';
                spinner.classList.add('hidden');
                const check = stepEl.querySelector('.check');
                check.classList.remove('hidden');
            } catch (err) {
                console.error(err);
                stepEl.className = 'progress-step failed';
                spinner.classList.add('hidden');
                stepEl.innerHTML += `<div class="error-msg">Error: ${err.message}</div>`;
                alert(`Analysis failed at step "${step.label}". Please verify your CSV format.`);
                return;
            }
        }

        // Complete final progress bar and redirect
        progressBarFill.style.width = '100%';
        await new Promise(resolve => setTimeout(resolve, 1000));
        window.location.href = '/report';
    });
});
