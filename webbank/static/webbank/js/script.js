// Add all the JavaScript content from the provided scripts.js file here
const toggleButton = document.getElementById('menu-toggle');
const sidebar = document.getElementById('sidebar');
const content = document.querySelector('.content');

// Toggle sidebar visibility
toggleButton.addEventListener('click', () => {
    sidebar.classList.toggle('show');
});

// Auto-close sidebar if clicked outside (on small screens)
document.addEventListener('click', (e) => {
    const isClickInsideSidebar = sidebar.contains(e.target);
    const isToggleBtn = toggleButton.contains(e.target);

    if (!isClickInsideSidebar && !isToggleBtn && window.innerWidth <= 768) {
        sidebar.classList.remove('show');
    }
});

document.addEventListener("DOMContentLoaded", function () {
  // Financial Chart using Chart.js
  const canvas = document.getElementById('financialChart');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
          {
            label: 'Revenue',
            data: [500000, 300000, 1000000, 400000, 600000, 450000],
            backgroundColor: '#0d1117'
          },
          {
            label: 'Expenses',
            data: [120000, 150000, 180000, 160000, 170000, 175000],
            backgroundColor: '#f1f5f9'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            ticks: {
              callback: function(value) {
                return '$' + value.toLocaleString();
              }
            },
            beginAtZero: true
          }
        }
      }
    });
  }

  // Tab functionality
  const buttons = document.querySelectorAll(".tab-button");
  const contents = document.querySelectorAll(".tab-content-section");

  buttons.forEach(button => {
    button.addEventListener("click", function () {
      // Remove 'active' from all buttons
      buttons.forEach(btn => btn.classList.remove("active"));
      // Add 'active' to clicked button
      this.classList.add("active");

      // Hide all content sections
      contents.forEach(section => section.classList.remove("active"));

      // Show the selected tab
      const targetId = this.getAttribute("data-target");
      const target = document.getElementById(targetId);
      if (target) {
        target.classList.add("active");
      }
    });
  });

  // Initialize with Overview tab active
  const activeTab = document.querySelector('.tab-button.active');
  if (activeTab) {
    activeTab.click();
  }
});