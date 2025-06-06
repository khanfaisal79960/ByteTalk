// static/js/main.js

console.log("ByteTalk: Where the bytes spill the tea! 😎");

document.addEventListener('DOMContentLoaded', () => {
    // --- Flash Message Dismissal (Bootstrap handles this, but ensures custom animation) ---
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.classList.add('animate__fadeInDown');
    });

    // --- Social Links Animation ---
    document.querySelectorAll('.social-links a').forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.textShadow = '0 0 15px var(--neon-yellow)';
        });
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.textShadow = 'none';
        });
    });

    // --- Button Click Pulse Animation ---
    document.querySelectorAll('.btn-neon-purple, .btn-neon-green-outline, .btn-neon-purple-outline, .btn-neon-blue-outline').forEach(button => {
        button.addEventListener('click', function() {
            this.classList.add('animate__pulse_click');
            setTimeout(() => {
                this.classList.remove('animate__pulse_click');
            }, 300);
        });
    });

    // --- Delete Confirmation ---
    document.querySelectorAll('.btn-delete-confirm').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const confirmDelete = confirm('Are you sure you want to delete this post? This action cannot be undone. 🚨');
            if (confirmDelete) {
                this.closest('form').submit();
            }
        });
    });

    // --- NEW: Theme Switcher Logic ---
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const body = document.body;

    // Function to set the theme based on the class
    function setTheme(isLightMode) {
        if (isLightMode) {
            body.classList.add('light-mode');
            themeIcon.innerHTML = `<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>`; // Moon icon (dark mode)
            localStorage.setItem('theme', 'light-mode');
        } else {
            body.classList.remove('light-mode');
            // Sun icon for dark mode (user wants to switch to light)
            themeIcon.innerHTML = `<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>`; // Sun icon (light mode)
            localStorage.setItem('theme', 'dark-mode');
        }
    }

    // Check for saved theme preference on page load
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light-mode') {
        setTheme(true); // Apply light mode if saved
    } else {
        setTheme(false); // Default to dark mode if no preference or saved dark mode
    }

    // Toggle theme on button click
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isLightMode = body.classList.contains('light-mode');
            setTheme(!isLightMode); // Toggle the theme
        });
    }
});