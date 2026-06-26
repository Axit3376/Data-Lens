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
});
