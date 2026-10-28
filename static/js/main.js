/**
 * Personal Expense Tracker - Main Frontend Logic
 * Handles Theme Toggling, Back Navigation, Password Visibility, Modals & Mobile Sidebar
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initBackButtons();
    initPasswordToggles();
    initMobileSidebar();
    initModals();
    initFlashAlerts();
});

// --------------------------------------------------------------------
// 1. Theme Management (Light / Dark Mode)
// --------------------------------------------------------------------
function initTheme() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = document.getElementById('theme-toggle-icon');
    const storedTheme = localStorage.getItem('pet_theme');

    // Default to stored theme or server preference
    if (storedTheme === 'dark' || (!storedTheme && document.documentElement.classList.contains('dark'))) {
        document.documentElement.classList.add('dark');
        if (themeIcon) {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
    } else {
        document.documentElement.classList.remove('dark');
        if (themeIcon) {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        }
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const isDark = document.documentElement.classList.toggle('dark');
            localStorage.setItem('pet_theme', isDark ? 'dark' : 'light');

            if (themeIcon) {
                if (isDark) {
                    themeIcon.classList.remove('fa-moon');
                    themeIcon.classList.add('fa-sun');
                } else {
                    themeIcon.classList.remove('fa-sun');
                    themeIcon.classList.add('fa-moon');
                }
            }
        });
    }
}

// --------------------------------------------------------------------
// 2. Safe Back Navigation Feature
// --------------------------------------------------------------------
function initBackButtons() {
    const backButtons = document.querySelectorAll('[data-action="go-back"]');
    backButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const fallback = btn.getAttribute('data-fallback') || '/dashboard';
            
            // Check if document referrer belongs to our origin
            if (document.referrer && document.referrer.includes(window.location.origin)) {
                window.history.back();
            } else {
                window.location.href = fallback;
            }
        });
    });
}

// --------------------------------------------------------------------
// 3. Password Visibility Toggle
// --------------------------------------------------------------------
function initPasswordToggles() {
    const toggles = document.querySelectorAll('[data-action="toggle-password"]');
    toggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const targetId = toggle.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            const icon = toggle.querySelector('i');

            if (targetInput) {
                if (targetInput.type === 'password') {
                    targetInput.type = 'text';
                    if (icon) {
                        icon.classList.remove('fa-eye');
                        icon.classList.add('fa-eye-slash');
                    }
                } else {
                    targetInput.type = 'password';
                    if (icon) {
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                    }
                }
            }
        });
    });
}

// --------------------------------------------------------------------
// 4. Mobile Navigation & Sidebar Drawer
// --------------------------------------------------------------------
function initMobileSidebar() {
    const toggleBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('app-sidebar');
    const overlay = document.getElementById('sidebar-backdrop');
    const closeBtn = document.getElementById('sidebar-close-btn');

    function openSidebar() {
        if (sidebar) sidebar.classList.remove('-translate-x-full');
        if (overlay) overlay.classList.remove('hidden');
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.add('-translate-x-full');
        if (overlay) overlay.classList.add('hidden');
    }

    if (toggleBtn) toggleBtn.addEventListener('click', openSidebar);
    if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);
}

// --------------------------------------------------------------------
// 5. Generic Modals (Details, Delete Confirmation, Logout)
// --------------------------------------------------------------------
function initModals() {
    // Open Modal Triggers
    document.querySelectorAll('[data-modal-target]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            const targetModalId = trigger.getAttribute('data-modal-target');
            const modal = document.getElementById(targetModalId);
            if (modal) {
                openModal(modal);

                // If it's a delete expense trigger, populate modal details
                if (trigger.hasAttribute('data-expense-id')) {
                    const expenseId = trigger.getAttribute('data-expense-id');
                    const expenseTitle = trigger.getAttribute('data-expense-title') || 'this expense';
                    const expenseAmount = trigger.getAttribute('data-expense-amount') || '';
                    
                    const form = modal.querySelector('form');
                    if (form) {
                        form.action = `/delete-expense/${expenseId}`;
                    }
                    const titleElem = modal.querySelector('#delete-modal-title');
                    if (titleElem) {
                        titleElem.textContent = expenseTitle;
                    }
                    const amtElem = modal.querySelector('#delete-modal-amount');
                    if (amtElem && expenseAmount) {
                        amtElem.textContent = expenseAmount;
                    }
                }

                // If it's a view details trigger, fetch via API
                if (trigger.hasAttribute('data-view-id')) {
                    const expenseId = trigger.getAttribute('data-view-id');
                    fetchExpenseDetails(expenseId, modal);
                }
            }
        });
    });

    // Close Modal Triggers
    document.querySelectorAll('[data-modal-close]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-overlay');
            if (modal) closeModal(modal);
        });
    });

    // Close on overlay backdrop click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeModal(overlay);
            }
        });
    });

    // Close on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                closeModal(modal);
            });
        }
    });
}

function openModal(modal) {
    modal.classList.add('active');
    document.body.classList.add('overflow-hidden');
}

function closeModal(modal) {
    modal.classList.remove('active');
    document.body.classList.remove('overflow-hidden');
}

// Fetch Expense Details via JSON endpoint
function fetchExpenseDetails(id, modal) {
    const titleEl = modal.querySelector('#detail-title');
    const amountEl = modal.querySelector('#detail-amount');
    const categoryEl = modal.querySelector('#detail-category');
    const dateEl = modal.querySelector('#detail-date');
    const notesEl = modal.querySelector('#detail-notes');
    const createdEl = modal.querySelector('#detail-created');
    const editLink = modal.querySelector('#detail-edit-link');

    if (titleEl) titleEl.textContent = 'Loading...';

    fetch(`/api/expense/${id}`)
        .then(res => res.json())
        .then(data => {
            if (titleEl) titleEl.textContent = data.title;
            if (amountEl) amountEl.textContent = data.formatted_amount;
            if (categoryEl) {
                categoryEl.innerHTML = `<i class="fa-solid ${data.category_icon} mr-1.5" style="color:${data.category_color}"></i> ${data.category_name}`;
            }
            if (dateEl) dateEl.textContent = data.expense_date;
            if (notesEl) notesEl.textContent = data.notes;
            if (createdEl) createdEl.textContent = data.created_at;
            if (editLink) editLink.href = `/edit-expense/${data.id}`;
        })
        .catch(err => {
            console.error('Error fetching details:', err);
            if (titleEl) titleEl.textContent = 'Error loading expense details.';
        });
}

// --------------------------------------------------------------------
// 6. Flash Alert Dismissal
// --------------------------------------------------------------------
function initFlashAlerts() {
    const alerts = document.querySelectorAll('.flash-banner');
    alerts.forEach(alert => {
        // Close button inside alert
        const closeBtn = alert.querySelector('[data-dismiss="alert"]');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 250);
            });
        }

        // Auto dismiss after 6 seconds
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 250);
            }
        }, 6000);
    });
}
