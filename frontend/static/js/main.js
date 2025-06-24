/**
 * BizFindr - Main JavaScript
 * Handles client-side interactions for the BizFindr application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Enable dropdowns
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function(dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
    
    // Handle refresh data button in navbar
    const refreshDataBtn = document.getElementById('refresh-data');
    if (refreshDataBtn) {
        refreshDataBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const btn = this;
            const originalText = btn.innerHTML;
            
            // Disable button and show loading state
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Refreshing...';
            
            // Make API call to refresh data
            fetch('/api/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Data refreshed successfully! ' + data.message, 'success');
                    // Reload the page to show updated data
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showAlert('Error: ' + (data.error || 'Failed to refresh data'), 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Error: ' + error.message, 'danger');
            })
            .finally(() => {
                // Re-enable button
                btn.disabled = false;
                btn.innerHTML = originalText;
            });
        });
    }
    
    // Handle form submissions with loading states
    const forms = document.querySelectorAll('form:not(.no-js)');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            
            if (submitBtn && !submitBtn.hasAttribute('data-no-loading')) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Processing...';
                
                // Revert button state after form submission completes
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 3000);
            }
        });
    });
    
    // Handle delete confirmation modals
    const deleteButtons = document.querySelectorAll('[data-bs-toggle="modal"][data-bs-target="#confirmDeleteModal"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-id');
            const targetName = this.getAttribute('data-name') || 'this item';
            const form = document.getElementById('deleteForm');
            
            if (form) {
                form.action = form.action.replace('/0', `/${targetId}`);
                document.getElementById('deleteItemName').textContent = targetName;
            }
        });
    });
    
    // Initialize date pickers
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        // Set max date to today
        input.max = new Date().toISOString().split('T')[0];
    });
    
    // Handle search form submission
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const query = this.querySelector('input[name="q"]').value.trim();
            const filters = Array.from(this.querySelectorAll('select, input')).filter(el => 
                el.name && el.name !== 'q' && el.value
            );
            
            if (!query && filters.length === 0) {
                e.preventDefault();
                showAlert('Please enter a search term or select at least one filter', 'warning');
                return false;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Searching...';
            }
        });
    }
    
    // Handle clear filters button
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const form = this.closest('form');
            if (form) {
                form.reset();
                form.submit();
            }
        });
    }
    
    // Handle tab persistence
    const tabLinks = document.querySelectorAll('a[data-bs-toggle="tab"]');
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            localStorage.setItem('activeTab', this.getAttribute('href'));
        });
        
        // Activate saved tab
        const activeTab = localStorage.getItem('activeTab');
        if (activeTab && link.getAttribute('href') === activeTab) {
            const tab = new bootstrap.Tab(link);
            tab.show();
        }
    });
    
    // Handle back to top button
    const backToTopBtn = document.getElementById('backToTop');
    if (backToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        });
        
        backToTopBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Update stats in navbar
    updateStats();
    
    // Set up periodic stats update
    setInterval(updateStats, 300000); // Update every 5 minutes
});

/**
 * Show a Bootstrap alert message
 * @param {string} message - The message to display
 * @param {string} type - The alert type (e.g., 'success', 'danger', 'warning', 'info')
 * @param {number} [duration=5000] - Duration to show the alert in milliseconds
 */
function showAlert(message, type = 'info', duration = 5000) {
    // Create alert element
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>`;
    
    // Add alert to the page
    const container = document.querySelector('.alerts-container') || document.querySelector('main') || document.body;
    const alertElement = document.createElement('div');
    alertElement.innerHTML = alertHtml;
    container.prepend(alertElement.firstElementChild);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            const alert = bootstrap.Alert.getOrCreateInstance(alertElement.querySelector('.alert'));
            if (alert) {
                alert.close();
            }
        }, duration);
    }
    
    // Handle alert close
    const closeBtn = alertElement.querySelector('.btn-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            const alert = bootstrap.Alert.getOrCreateInstance(this.closest('.alert'));
            if (alert) {
                alert.close();
            }
        });
    }
}

/**
 * Update stats in the navbar
 */
function updateStats() {
    const statsElement = document.getElementById('stats-count');
    if (!statsElement) return;
    
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            if (data && data.total_registrations !== undefined) {
                statsElement.textContent = data.total_registrations.toLocaleString() + ' records';
            }
        })
        .catch(error => console.error('Error fetching stats:', error));
}

/**
 * Initialize charts using Chart.js
 */
function initializeCharts() {
    // Business Types Chart
    const businessTypesCtx = document.getElementById('businessTypesChart');
    if (businessTypesCtx) {
        const data = JSON.parse(businessTypesCtx.getAttribute('data-chart-data') || '{}');
        
        if (data.labels && data.datasets) {
            new Chart(businessTypesCtx, {
                type: 'doughnut',
                data: data,
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    cutout: '70%',
                }
            });
        }
    }
    
    // Registration Trends Chart
    const trendsCtx = document.getElementById('registrationTrendsChart');
    if (trendsCtx) {
        const data = JSON.parse(trendsCtx.getAttribute('data-chart-data') || '{}');
        
        if (data.labels && data.datasets) {
            new Chart(trendsCtx, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += context.parsed.y.toLocaleString();
                                    }
                                    return label;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
}

/**
 * Format a date string to a more readable format
 * @param {string} dateString - The date string to format
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return new Date(dateString).toLocaleDateString('en-US', options);
}

/**
 * Debounce function to limit how often a function can be called
 * @param {Function} func - The function to debounce
 * @param {number} wait - The time to wait in milliseconds
 * @returns {Function} The debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Make functions available globally
window.showAlert = showAlert;
window.formatDate = formatDate;
