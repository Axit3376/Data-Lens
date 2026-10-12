document.addEventListener('DOMContentLoaded', () => {
    // ==========================================
    // 1. TABS SYSTEM (Feature Engineering)
    // ==========================================
    window.openTab = function(event, tabName) {
        const parentSection = event.currentTarget.closest('.report-section');
        
        // Hide every tab content in this section
        parentSection.querySelectorAll(".tab-content")
            .forEach(tab => {
                tab.style.display = "none";
                tab.classList.remove("active");
            });

        // Remove active class from buttons
        parentSection.querySelectorAll(".tab-btn")
            .forEach(btn => btn.classList.remove("active"));

        // Show selected tab content
        const activeTab = parentSection.querySelector(`#${tabName}`);
        if (activeTab) {
            activeTab.style.display = "block";
            setTimeout(() => activeTab.classList.add("active"), 10);
        }

        // Activate button
        event.currentTarget.classList.add("active");
    };

    // Open first tab automatically on load
    const firstTabBtn = document.querySelector('.tab-btn');
    if (firstTabBtn) {
        firstTabBtn.click();
    }

    // ==========================================
    // 2. THEME SWITCHER (Dark / Light Mode)
    // ==========================================
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

    // ==========================================
    // 3. SIDEBAR SMOOTH SCROLL & SCROLL SPY
    // ==========================================
    const sidebarLinks = document.querySelectorAll('.sidebar-nav a');
    const sections = Array.from(sidebarLinks).map(link => {
        const id = link.getAttribute('href').substring(1);
        return document.getElementById(id);
    }).filter(el => el !== null);

    // Scroll Spy active navigation highlight
    function updateActiveLink() {
        const scrollPosition = window.scrollY + 120; // offset for sticky headers

        let currentSectionId = '';
        for (const section of sections) {
            const top = section.offsetTop;
            const height = section.offsetHeight;
            if (scrollPosition >= top && scrollPosition < top + height) {
                currentSectionId = section.getAttribute('id');
            }
        }

        sidebarLinks.forEach(link => {
            const href = link.getAttribute('href').substring(1);
            if (href === currentSectionId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    window.addEventListener('scroll', updateActiveLink);
    updateActiveLink(); // Initial run

    // Smooth scroll offset adjustments
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetEl = document.getElementById(targetId);
            if (targetEl) {
                const offsetPosition = targetEl.offsetTop - 80;
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // ==========================================
    // 4. VISUALIZATION GALLERY / CAROUSEL SYSTEM
    // ==========================================
    // We can have multiple carousels on the page. We will initialize each.
    const initializeCarousels = () => {
        const carouselContainers = document.querySelectorAll('.carousel-container-wrapper');
        
        carouselContainers.forEach(container => {
            const track = container.querySelector('.carousel-track');
            const slides = container.querySelectorAll('.carousel-slide');
            const prevBtn = container.querySelector('.carousel-btn.prev');
            const nextBtn = container.querySelector('.carousel-btn.next');
            const dotsContainer = container.querySelector('.carousel-dots');
            
            if (slides.length === 0) return;
            
            if (slides.length <= 1) {
                if (prevBtn) prevBtn.style.display = 'none';
                if (nextBtn) nextBtn.style.display = 'none';
                if (dotsContainer) dotsContainer.style.display = 'none';
            }
            
            let currentIndex = 0;
            const maxIndex = slides.length - 1;

            // Generate dots if container exists
            if (dotsContainer) {
                dotsContainer.innerHTML = '';
                slides.forEach((_, idx) => {
                    const dot = document.createElement('span');
                    dot.className = `dot ${idx === 0 ? 'active' : ''}`;
                    dot.addEventListener('click', () => goToSlide(idx));
                    dotsContainer.appendChild(dot);
                });
            }

            const dots = dotsContainer ? dotsContainer.querySelectorAll('.dot') : [];

            function updateCarousel() {
                // Shift track
                track.style.transform = `translateX(-${currentIndex * 100}%)`;
                
                // Update dots
                dots.forEach((dot, idx) => {
                    if (idx === currentIndex) {
                        dot.classList.add('active');
                    } else {
                        dot.classList.remove('active');
                    }
                });

                // Update button disabled state (optional: loop instead)
                // For a looping carousel:
                if (prevBtn) prevBtn.disabled = false;
                if (nextBtn) nextBtn.disabled = false;
            }

            function goToSlide(index) {
                currentIndex = index;
                if (currentIndex < 0) currentIndex = maxIndex;
                if (currentIndex > maxIndex) currentIndex = 0;
                updateCarousel();
            }

            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    goToSlide(currentIndex - 1);
                });
            }

            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    goToSlide(currentIndex + 1);
                });
            }

            // Setup track layout: force horizontal
            track.style.display = 'flex';
            track.style.transition = 'transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
            slides.forEach(slide => {
                slide.style.flex = '0 0 100%';
                slide.style.boxSizing = 'border-box';
            });
        });
    };

    initializeCarousels();

    // Visualizations category tab switching
    const vizTabs = document.querySelectorAll('.viz-tab-btn');
    const vizPanels = document.querySelectorAll('.viz-tab-panel');

    vizTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.getAttribute('data-target');
            
            vizTabs.forEach(btn => btn.classList.remove('active'));
            vizPanels.forEach(panel => {
                panel.classList.remove('active');
                panel.style.display = 'none';
            });
            
            tab.classList.add('active');
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.style.display = 'block';
                // Trigger reflow/animation
                setTimeout(() => targetPanel.classList.add('active'), 10);
            }
        });
    });

    // Open first visualization tab
    const firstVizTab = document.querySelector('.viz-tab-btn');
    if (firstVizTab) {
        firstVizTab.click();
    }

    // ==========================================
    // 5. SMART DATA CLEANING WORKSPACE CONTROLLER
    // ==========================================
    const recsContainer = document.getElementById('recommendations-container');
    const previewPanel = document.getElementById('preview-panel');
    const btnPreview = document.getElementById('btn-preview-cleaning');
    const btnClosePreview = document.getElementById('btn-close-preview');
    const btnCancelPreview = document.getElementById('btn-cancel-preview');
    const btnConfirmApply = document.getElementById('btn-confirm-apply');
    const btnUndo = document.getElementById('btn-undo-cleaning');
    const btnSelectAll = document.getElementById('btn-select-all-recs');
    const btnClearAll = document.getElementById('btn-clear-recs');
    const historyTbody = document.getElementById('cleaning-history-tbody');

    let currentSessionId = 'default_session';
    let currentRecommendations = [];
    let activePreviewId = null;

    // Load Cleaning Analysis & Recommendations
    async function loadCleaningWorkspace() {
        if (!recsContainer) return;
        try {
            const resp = await fetch(`/cleaning/analyze?session_id=${currentSessionId}`);
            if (resp.ok) {
                const data = await resp.json();
                currentRecommendations = data.recommendations || [];
                updateVersionUI(data.current_version, data.history);
                updateQualityScoreUI(data.quality_score);
                renderRecommendations(currentRecommendations);
                return;
            }
            // If backend returned non-200, check if recommendations exist in window / server-rendered state
            const renderedCards = recsContainer.querySelectorAll('.rec-item-card');
            if (renderedCards.length === 0) {
                recsContainer.innerHTML = `<div style="padding: 20px; color: var(--text-muted);">Please upload a CSV dataset on the home page first to activate smart cleaning tools.</div>`;
            }
        } catch (err) {
            console.error("Error loading cleaning recommendations:", err);
            const renderedCards = recsContainer.querySelectorAll('.rec-item-card');
            if (renderedCards.length === 0) {
                recsContainer.innerHTML = `<div style="padding: 20px; color: var(--danger-text);">Failed to load recommendations: ${err.message}</div>`;
            }
        }
    }

    function updateVersionUI(version, history) {
        const vBadge = document.getElementById('active-dataset-version');
        const vMeta = document.getElementById('active-dataset-meta');
        if (vBadge) {
            vBadge.textContent = `v${version} ${version === 0 ? '(Original)' : '(Cleaned)'}`;
        }
        if (vMeta) {
            vMeta.textContent = version === 0 
                ? 'Original dataset preserved safely.' 
                : `Currently using cleaned dataset iteration #${version}.`;
        }
        if (historyTbody && history) {
            historyTbody.innerHTML = '';
            history.forEach(item => {
                const tr = document.createElement('tr');
                const summaryStr = Array.isArray(item.summary) ? item.summary.join(', ') : (item.summary || 'Cleaning batch applied');
                tr.innerHTML = `
                    <td><span class="badge" style="background: var(--bg-secondary); color: var(--text-primary);">v${item.version}</span></td>
                    <td>${item.timestamp ? item.timestamp.split('T')[0] + ' ' + item.timestamp.split('T')[1].substring(0, 8) : 'Initial'}</td>
                    <td>${item.operation_id || 'upload'}</td>
                    <td>${summaryStr}</td>
                `;
                historyTbody.appendChild(tr);
            });
        }
    }

    function updateQualityScoreUI(scoreData) {
        if (!scoreData) return;
        const liveScore = document.getElementById('live-overall-score');
        const liveRating = document.getElementById('live-overall-rating');
        if (liveScore && scoreData.overall_score !== null) {
            liveScore.textContent = scoreData.overall_score;
            liveScore.style.color = scoreData.rating_color;
        }
        if (liveRating) {
            liveRating.textContent = scoreData.rating;
            liveRating.style.color = scoreData.rating_color;
        }

        ['completeness', 'validity', 'uniqueness', 'consistency'].forEach(dim => {
            const valEl = document.getElementById(`live-score-${dim}`);
            const barEl = document.getElementById(`live-bar-${dim}`);
            const dimData = scoreData.dimensions ? scoreData.dimensions[dim] : null;
            if (valEl && dimData && dimData.score !== null) {
                valEl.textContent = `${dimData.score}%`;
            }
            if (barEl && dimData && dimData.score !== null) {
                barEl.style.width = `${dimData.score}%`;
                barEl.style.background = dimData.score >= 85 ? 'var(--success-text)' : (dimData.score >= 60 ? 'var(--warning-text)' : 'var(--danger-text)');
            }
        });
    }

    function renderRecommendations(recs) {
        if (!recsContainer) return;
        if (!recs || recs.length === 0) {
            recsContainer.innerHTML = `
                <div style="text-align: center; padding: 25px; color: var(--success-text); font-weight: 500;">
                    ✨ Clean bill of health! No critical data quality issues flagged for cleaning.
                </div>
            `;
            if (btnPreview) btnPreview.disabled = true;
            return;
        }

        if (btnPreview) btnPreview.disabled = false;
        recsContainer.innerHTML = '';
        
        recs.forEach((rec, idx) => {
            const card = document.createElement('div');
            card.className = 'rec-item-card';
            card.style.cssText = `
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: 16px 20px;
                background: var(--bg-primary);
                display: flex;
                flex-direction: column;
                gap: 12px;
                transition: var(--transition-smooth);
            `;

            const sevBadge = rec.severity === 'high' 
                ? '<span class="badge danger">High Severity</span>' 
                : (rec.severity === 'medium' ? '<span class="badge warning">Medium</span>' : '<span class="badge success">Low</span>');

            const optionsHtml = rec.allowed_actions.map(opt => `
                <option value="${opt.action}" ${opt.action === rec.proposed_action ? 'selected' : ''}>${opt.label}</option>
            `).join('');

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <input type="checkbox" id="rec-chk-${idx}" class="rec-checkbox" data-idx="${idx}" checked style="width: 18px; height: 18px; cursor: pointer; accent-color: var(--accent-primary);">
                        <div>
                            <strong style="font-size: 0.95rem; color: var(--text-primary);">${rec.column ? `Column [${rec.column}]` : 'Dataset-wide'}: ${rec.issue_type.replace('_', ' ').toUpperCase()}</strong>
                            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 2px;">${rec.rationale}</div>
                        </div>
                    </div>
                    <div>${sevBadge}</div>
                </div>

                <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; background: var(--bg-card); padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-secondary);">Action:</span>
                        <select class="rec-action-select" data-idx="${idx}" style="padding: 6px 10px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); background: var(--bg-primary); color: var(--text-primary); font-size: 0.85rem;">
                            ${optionsHtml}
                        </select>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--warning-text); display: flex; align-items: center; gap: 4px;">
                        <span>⚠️ ${rec.warning}</span>
                    </div>
                </div>
            `;
            recsContainer.appendChild(card);
        });
    }

    if (btnSelectAll) {
        btnSelectAll.addEventListener('click', () => {
            document.querySelectorAll('.rec-checkbox').forEach(chk => chk.checked = true);
        });
    }

    if (btnClearAll) {
        btnClearAll.addEventListener('click', () => {
            document.querySelectorAll('.rec-checkbox').forEach(chk => chk.checked = false);
        });
    }

    // Build Cleaning Plan from UI
    function getSelectedCleaningPlan() {
        const operations = [];
        const chks = document.querySelectorAll('.rec-checkbox:checked');
        chks.forEach(chk => {
            const idx = parseInt(chk.getAttribute('data-idx'));
            const rec = currentRecommendations[idx];
            const selectEl = document.querySelector(`.rec-action-select[data-idx="${idx}"]`);
            const chosenAction = selectEl ? selectEl.value : rec.proposed_action;

            operations.push({
                action: chosenAction,
                column: rec.column,
                parameters: rec.parameters || {}
            });
        });
        return operations;
    }

    // Preview Button Action
    if (btnPreview) {
        btnPreview.addEventListener('click', async () => {
            const ops = getSelectedCleaningPlan();
            if (ops.length === 0) {
                alert('Please select at least one cleaning recommendation to preview.');
                return;
            }

            btnPreview.disabled = true;
            btnPreview.textContent = 'Generating Preview...';

            try {
                const resp = await fetch('/cleaning/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        operations: ops
                    })
                });

                if (!resp.ok) {
                    const err = await resp.json();
                    throw new Error(err.detail || 'Preview generation failed.');
                }

                const data = await resp.json();
                activePreviewId = data.preview_id;
                renderPreview(data);
            } catch (err) {
                alert(`Error: ${err.message}`);
            } finally {
                btnPreview.disabled = false;
                btnPreview.textContent = '👁️ Preview Selected Changes';
            }
        });
    }

    function renderPreview(data) {
        if (!previewPanel) return;
        previewPanel.style.display = 'block';
        previewPanel.scrollIntoView({ behavior: 'smooth' });

        document.getElementById('preview-score-before').textContent = data.score_before.overall_score || 'N/A';
        document.getElementById('preview-score-after').textContent = data.score_after.overall_score || 'N/A';
        document.getElementById('preview-rows-summary').textContent = `${data.summary.initial_rows} → ${data.summary.final_rows} (-${data.summary.rows_removed})`;
        document.getElementById('preview-cells-summary').textContent = `${data.summary.changed_cells} cells`;

        const opsList = document.getElementById('preview-operations-list');
        if (opsList) {
            opsList.innerHTML = '';
            data.summary.operations_executed.forEach(opMsg => {
                const li = document.createElement('li');
                li.textContent = opMsg;
                opsList.appendChild(li);
            });
        }

        // Render sample table
        const thead = document.getElementById('preview-table-headers');
        const tbody = document.getElementById('preview-table-body');
        if (thead && tbody && data.sample_after && data.sample_after.length > 0) {
            const cols = Object.keys(data.sample_after[0]);
            thead.innerHTML = cols.map(c => `<th style="padding: 6px 10px;">${c}</th>`).join('');
            tbody.innerHTML = data.sample_after.map(row => `
                <tr>
                    ${cols.map(c => `<td style="padding: 6px 10px;">${row[c] !== null && row[c] !== undefined ? row[c] : '<em style="color:var(--text-muted)">NaN</em>'}</td>`).join('')}
                </tr>
            `).join('');
        }
    }

    if (btnClosePreview) {
        btnClosePreview.addEventListener('click', () => {
            if (previewPanel) previewPanel.style.display = 'none';
        });
    }

    if (btnCancelPreview) {
        btnCancelPreview.addEventListener('click', () => {
            if (previewPanel) previewPanel.style.display = 'none';
        });
    }

    // Confirm Apply Action
    if (btnConfirmApply) {
        btnConfirmApply.addEventListener('click', async () => {
            if (!activePreviewId) {
                alert('No active preview found.');
                return;
            }

            btnConfirmApply.disabled = true;
            btnConfirmApply.textContent = 'Applying Cleaning Plan...';

            try {
                const resp = await fetch('/cleaning/apply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        preview_id: activePreviewId
                    })
                });

                if (!resp.ok) {
                    const err = await resp.json();
                    throw new Error(err.detail || 'Apply operation failed.');
                }

                const resData = await resp.json();
                alert(`Successfully cleaned dataset! New version: v${resData.current_version}`);
                if (previewPanel) previewPanel.style.display = 'none';
                activePreviewId = null;
                // Reload cleaning recommendations and scores
                await loadCleaningWorkspace();
            } catch (err) {
                alert(`Error applying cleaning: ${err.message}`);
            } finally {
                btnConfirmApply.disabled = false;
                btnConfirmApply.textContent = '✓ Confirm & Apply Cleaning Plan';
            }
        });
    }

    // Undo Action
    if (btnUndo) {
        btnUndo.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to revert the latest cleaning operation?')) return;
            try {
                const resp = await fetch('/cleaning/undo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: currentSessionId })
                });

                if (!resp.ok) {
                    const err = await resp.json();
                    throw new Error(err.detail || 'Undo failed.');
                }

                const resData = await resp.json();
                alert(`Reverted dataset to version v${resData.current_version}`);
                if (previewPanel) previewPanel.style.display = 'none';
                await loadCleaningWorkspace();
            } catch (err) {
                alert(`Undo Error: ${err.message}`);
            }
        });
    }

    // Initial load of cleaning workspace
    loadCleaningWorkspace();
});

