/**
 * main.js – Smart Ticket Prioritization System
 * Global JS: tooltips, navbar scroll effect, theme utilities
 */

'use strict';

/* ── Bootstrap tooltips ─────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Activate all Bootstrap tooltips
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el, { trigger: 'hover' });
  });

  // Navbar scroll effect
  const nav = document.querySelector('.glass-nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.style.boxShadow = window.scrollY > 40
        ? '0 4px 30px rgba(0,0,0,0.5)'
        : 'none';
    }, { passive: true });
  }

  // Auto-dismiss flash alerts after 5s
  document.querySelectorAll('.alert.fade.show').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Smooth reveal on scroll (IntersectionObserver)
  const revealEls = document.querySelectorAll(
    '.feature-card, .step-card, .kpi-card, .glass-card'
  );
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.style.opacity = '1';
          e.target.style.transform = 'translateY(0)';
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    revealEls.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      io.observe(el);
    });
  }
});

/* ── Utility: copy text to clipboard ──────────────────────── */
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!', 'success');
  });
}

/* ── Simple toast notification ────────────────────────────── */
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer') || createToastContainer();
  const id = `toast-${Date.now()}`;
  const colorMap = { success: '#22c55e', danger: '#ef4444', info: '#6366f1', warning: '#f59e0b' };
  const toast = document.createElement('div');
  toast.id = id;
  toast.style.cssText = `
    background: rgba(15,23,42,0.95);
    border: 1px solid ${colorMap[type] || colorMap.info}44;
    border-left: 3px solid ${colorMap[type] || colorMap.info};
    color: #f1f5f9;
    padding: 12px 20px;
    border-radius: 10px;
    font-size: 0.88rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    opacity: 0;
    transform: translateX(20px);
    transition: all 0.3s ease;
    margin-top: 8px;
    max-width: 320px;
  `;
  toast.textContent = message;
  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(0)';
  });
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 350);
  }, 3500);
}

function createToastContainer() {
  const div = document.createElement('div');
  div.id = 'toastContainer';
  div.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;';
  document.body.appendChild(div);
  return div;
}
