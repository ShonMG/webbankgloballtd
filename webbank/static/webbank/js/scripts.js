document.addEventListener('DOMContentLoaded', function () {
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    const content = document.querySelector('.content');

    // Function to toggle sidebar visibility and overlay
    function toggleSidebar() {
        sidebar.classList.toggle('show');
        sidebarOverlay.classList.toggle('show');
    }

    if (menuToggle) {
        menuToggle.addEventListener('click', function () {
            toggleSidebar();
        });
    }

    if (sidebarOverlay) {
        // Hide sidebar and overlay when clicking outside on mobile
        sidebarOverlay.addEventListener('click', function () {
            toggleSidebar();
        });
    }


    // Optional: Close sidebar if screen size changes from mobile to desktop while open
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) { // Desktop size
            if (sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
                sidebarOverlay.classList.remove('show');
            }
        }
    });

    // Animate cards on scroll using Intersection Observer
    const cards = document.querySelectorAll('.card');
    if (cards.length > 0) {
        const observerOptions = {
            root: null, // viewport
            rootMargin: '0px',
            threshold: 0.1 // 10% of card visible triggers animation
        };

        const cardObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Check if the card already has animation classes to avoid re-animating
                    if (!entry.target.classList.contains('animate__animated')) {
                        // Apply animation classes
                        entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                        // Add delay if defined, otherwise animate immediately
                        const delay = entry.target.dataset.animationDelay;
                        if (delay) {
                            entry.target.style.animationDelay = delay;
                        }
                    }
                    observer.unobserve(entry.target); // Stop observing once animated
                }
            });
        }, observerOptions);

        cards.forEach(card => {
            // Check if card already has animation classes, if so, just observe (useful for cards loaded with delays already)
            if (!card.classList.contains('animate__animated')) {
                cardObserver.observe(card);
            }
        });
    } // CLOSING BRACE ADDED HERE
    
    // Script from shares.html for calculating total amount in Share Purchase Modal
    const unitsInput = document.querySelector('#id_units');
    const totalAmount = document.querySelector('#totalAmount');
    
    if (unitsInput && totalAmount) {
        unitsInput.addEventListener('input', function() {
            const units = parseInt(this.value) || 0;
            totalAmount.textContent = (units * 100).toLocaleString();
        });
    }
});