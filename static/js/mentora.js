/**
 * MENTORA — Application Client JavaScript
 * Vasumathi Ramaswami Centenary Foundation (VRCF)
 */

window.Mentora = (function() {
  'use strict';


  // Mobile sidebar drawer
  function initMobileSidebar() {
    const toggleBtn = document.getElementById('mobileSidebarToggle');
    const sidebar = document.querySelector('.mentora-sidebar');
    const overlay = document.getElementById('mobileOverlay');

    if (toggleBtn && sidebar && overlay) {
      toggleBtn.addEventListener('click', function() {
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('active');
      });

      overlay.addEventListener('click', function() {
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
      });

      // Close on navigation link click on mobile
      const navLinks = sidebar.querySelectorAll('.sidebar-nav-item');
      navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
          if (window.innerWidth <= 992) {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
          }
        });
      });
    }
  }

  // CSRF token retrieval helper
  function getCsrfToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) return csrfInput.value;

    const cookieValue = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
    return cookieValue || '';
  }

  // Toast notification system
  function showToast(message, type = 'info', duration = 4000) {
    let toastContainer = document.getElementById('mentoraToastContainer');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'mentoraToastContainer';
      toastContainer.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;';
      document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    const bgColors = {
      success: 'var(--status-success)',
      danger: 'var(--status-danger)',
      warning: 'var(--status-warning)',
      info: 'var(--primary-accent)'
    };

    toast.style.cssText = `
      background-color: var(--bg-surface);
      color: var(--text-primary);
      border-left: 4px solid ${bgColors[type] || bgColors.info};
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-lg);
      padding: 12px 18px;
      font-size: 0.9rem;
      min-width: 280px;
      max-width: 420px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      transform: translateY(20px);
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    `;

    toast.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px;">
        <i class="bi ${type === 'success' ? 'bi-check-circle-fill text-success' : type === 'danger' ? 'bi-exclamation-octagon-fill text-danger' : 'bi-info-circle-fill text-primary'}"></i>
        <span>${message}</span>
      </div>
      <button type="button" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1.1rem;padding:0;" onclick="this.parentElement.remove()">&times;</button>
    `;

    toastContainer.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.transform = 'translateY(0)';
      toast.style.opacity = '1';
    });

    setTimeout(() => {
      toast.style.transform = 'translateY(20px)';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  // Notification mark-all-read and badge clearance
  function initNotifications() {
    const dropdownToggle = document.getElementById('notifDropdownToggle');
    const badge = document.getElementById('notifBadge');
    const headerBadge = document.getElementById('notifHeaderBadge');
    const markAllBtn = document.getElementById('markAllNotifBtn');

    function clearNotificationBadges() {
      if (badge) {
        badge.style.display = 'none';
      }
      if (headerBadge) {
        headerBadge.style.display = 'none';
      }
      // Send background request to mark all read
      fetch('/api/notifications/mark-all-read/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'Content-Type': 'application/json'
        }
      }).catch(function() {});
    }

    if (dropdownToggle) {
      dropdownToggle.addEventListener('show.bs.dropdown', clearNotificationBadges);
      dropdownToggle.addEventListener('click', function() {
        if (badge && badge.style.display !== 'none') {
          clearNotificationBadges();
        }
      });
    }

    if (markAllBtn) {
      markAllBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        clearNotificationBadges();
      });
    }

    // Individual notification clicks
    const notifLinks = document.querySelectorAll('.notif-link');
    notifLinks.forEach(function(link) {
      link.addEventListener('click', function() {
        const notifId = this.getAttribute('data-notif-id');
        if (notifId) {
          fetch(`/api/notifications/${notifId}/read/`, {
            method: 'POST',
            headers: {
              'X-CSRFToken': getCsrfToken(),
              'Content-Type': 'application/json'
            }
          }).catch(function() {});
        }
      });
    });
  }

  // Register PWA Service Worker
  function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
          .then(reg => {
            // console.log('Mentora SW registered:', reg.scope);
          })
          .catch(err => {
            // console.log('Mentora SW registration failed:', err);
          });
      });
    }
  }

  // Initialize on DOM ready
  document.addEventListener('DOMContentLoaded', function() {
    try {
      localStorage.removeItem('mentora_theme');
      document.cookie = 'mentora_theme=light; path=/; max-age=0;';
      document.documentElement.setAttribute('data-theme', 'light');
    } catch (e) {}
    initMobileSidebar();
    initNotifications();
    registerServiceWorker();
  });

  return {
    getCsrfToken: getCsrfToken,
    showToast: showToast
  };
})();
