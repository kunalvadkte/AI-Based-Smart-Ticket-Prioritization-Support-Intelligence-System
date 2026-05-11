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

/* ── Floating Mail Ticket Composer ──────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('mailComposerBtn');
  const popup = document.getElementById('mailComposerPopup');
  const closeBtn = document.getElementById('mailComposerClose');
  const minBtn = document.getElementById('mailComposerMinimize');
  const advToggle = document.getElementById('mailAdvancedToggle');
  const advOptions = document.getElementById('mailAdvancedOptions');
  const genBtn = document.getElementById('mailGenerateTicketBtn');

  if(btn && popup) {
    function resetComposeForm() {
      const mailCustomer = document.getElementById('mailCustomer');
      const mailSubject = document.getElementById('mailSubject');
      const mailBody = document.getElementById('mailBody');
      
      if (mailCustomer) mailCustomer.value = '';
      if (mailSubject) mailSubject.value = '';
      if (mailBody) {
        mailBody.value = '';
        mailBody.style.height = '120px';
      }

      const issueType = document.getElementById('mailIssueType');
      if (issueType) { issueType.value = 'Technical Bug'; issueType.style.backgroundColor = 'transparent'; }
      
      const impactLevel = document.getElementById('mailImpactLevel');
      if (impactLevel) { impactLevel.value = 'Medium'; impactLevel.style.backgroundColor = 'transparent'; }

      const customerType = document.getElementById('mailCustomerType');
      if (customerType) customerType.value = 'Regular';
      
      const channel = document.getElementById('mailChannel');
      if (channel) channel.value = 'Email';
      
      const prevComplaints = document.getElementById('mailPrevComplaints');
      if (prevComplaints) prevComplaints.value = '0';
      
      const hoursOpen = document.getElementById('mailHoursOpen');
      if (hoursOpen) hoursOpen.value = '1';

      if (advOptions && advOptions.classList.contains('show')) {
        advOptions.classList.remove('show');
        if (advToggle) advToggle.innerHTML = '<i class="bi bi-sliders2"></i> Show Advanced Metadata';
      }
    }

    btn.addEventListener('click', () => {
      resetComposeForm(); // Clean state before opening
      popup.style.transition = 'none';
      popup.style.opacity = '0';
      popup.classList.add('active');
      
      // Smooth fade-in
      setTimeout(() => {
        popup.style.transition = 'transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease';
        popup.style.opacity = '1';
      }, 10);
    });

    closeBtn.addEventListener('click', () => {
      popup.style.opacity = '0';
      popup.classList.remove('active');
      setTimeout(resetComposeForm, 400); // Wait for transition
    });
    
    minBtn.addEventListener('click', () => {
      popup.style.opacity = '0';
      popup.classList.remove('active');
      setTimeout(resetComposeForm, 400);
    });

    // Close on click outside
    document.addEventListener('mousedown', (e) => {
      if (popup.classList.contains('active') && !popup.contains(e.target) && !btn.contains(e.target)) {
        popup.style.opacity = '0';
        popup.classList.remove('active');
        setTimeout(resetComposeForm, 400);
      }
    });

    if(advToggle && advOptions) {
      advToggle.addEventListener('click', () => {
        advOptions.classList.toggle('show');
        if(advOptions.classList.contains('show')){
          advToggle.innerHTML = '<i class="bi bi-sliders2"></i> Hide Advanced Metadata';
        } else {
          advToggle.innerHTML = '<i class="bi bi-sliders2"></i> Show Advanced Metadata';
        }
      });
    }

    // Auto-expand textarea
    const mailBody = document.getElementById('mailBody');
    if(mailBody) {
      mailBody.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
      });
    }

    // Smart Suggestions
    document.querySelectorAll('.mail-suggestion-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        // Typewriter effect for subject and body
        typeWriterEffect(document.getElementById('mailSubject'), chip.dataset.sub, () => {
          typeWriterEffect(document.getElementById('mailBody'), chip.dataset.body, () => {
            if(mailBody) {
              mailBody.style.height = 'auto';
              mailBody.style.height = (mailBody.scrollHeight) + 'px';
            }
            autoExtractKeywords();
          });
        });
      });
    });

    // Auto extraction logic on typing
    if(mailBody) {
      mailBody.addEventListener('keyup', autoExtractKeywords);
    }
    const mailSubject = document.getElementById('mailSubject');
    if(mailSubject) {
      mailSubject.addEventListener('keyup', autoExtractKeywords);
    }

    function autoExtractKeywords() {
      const text = (document.getElementById('mailSubject').value + " " + document.getElementById('mailBody').value).toLowerCase();
      
      let issueType = "Technical Bug";
      let impactLevel = "Medium";

      if(text.includes('server down') || text.includes('offline') || text.includes('production halted')) {
        issueType = "Server Down";
        impactLevel = "High";
      } else if (text.includes('payment') || text.includes('deducted') || text.includes('refund')) {
        issueType = "Payment Issue";
        impactLevel = "High";
      } else if (text.includes('login') || text.includes('password') || text.includes('access')) {
        issueType = "Login Issue";
      } else if (text.includes('feature') || text.includes('request') || text.includes('add')) {
        issueType = "Feature Request";
        impactLevel = "Low";
      } else if (text.includes('security') || text.includes('hack') || text.includes('breach')) {
        issueType = "Security Problem";
        impactLevel = "High";
      } else if (text.includes('crash') || text.includes('bug') || text.includes('error')) {
        issueType = "Technical Bug";
        impactLevel = "Medium";
      }

      const issueSelect = document.getElementById('mailIssueType');
      const impactSelect = document.getElementById('mailImpactLevel');
      
      if (issueSelect.value !== issueType) {
        issueSelect.value = issueType;
        flashField(issueSelect);
      }
      if (impactSelect.value !== impactLevel) {
        impactSelect.value = impactLevel;
        flashField(impactSelect);
      }
    }

    function flashField(element) {
      element.style.transition = 'background-color 0.3s';
      element.style.backgroundColor = 'rgba(99,102,241,0.3)';
      setTimeout(() => {
        element.style.backgroundColor = 'transparent';
      }, 500);
    }

    function typeWriterEffect(element, text, callback, i = 0) {
      if (i === 0) element.value = '';
      if (i < text.length) {
        element.value += text.charAt(i);
        setTimeout(() => typeWriterEffect(element, text, callback, i + 1), 20); // typing speed
      } else {
        if(callback) callback();
      }
    }

    // Generate Ticket Click
    if(genBtn) {
      genBtn.addEventListener('click', () => {
        const ticketData = {
          title: document.getElementById('mailSubject').value,
          description: document.getElementById('mailBody').value,
          issue_type: document.getElementById('mailIssueType').value,
          customer_type: document.getElementById('mailCustomerType').value,
          channel: document.getElementById('mailChannel').value,
          impact_level: document.getElementById('mailImpactLevel').value,
          previous_complaints: document.getElementById('mailPrevComplaints').value,
          hours_open: document.getElementById('mailHoursOpen').value
        };

        // Save to sessionStorage
        sessionStorage.setItem('pendingTicketData', JSON.stringify(ticketData));
        
        // Show loading state
        const originalBtnHtml = genBtn.innerHTML;
        genBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Analyzing...';
        
        setTimeout(() => {
          // Check if we are on predict page
          if(window.location.pathname.includes('/predict')) {
            fillPredictForm();
            popup.style.opacity = '0';
            popup.classList.remove('active');
            genBtn.innerHTML = originalBtnHtml;
            setTimeout(resetComposeForm, 400); // Clear state after success
            
            // Scroll to form and highlight
            const formObj = document.getElementById('ticketForm');
            if(formObj) {
               formObj.scrollIntoView({ behavior: 'smooth' });
               formObj.classList.add('glow-highlight');
               setTimeout(() => formObj.classList.remove('glow-highlight'), 2000);
            }
          } else {
            // Redirect to predict page
            window.location.href = '/predict';
          }
        }, 1200);
      });
    }
  }

  // Check on load if pending data exists to fill the form
  if(window.location.pathname.includes('/predict')) {
    fillPredictForm();
  }
});

function fillPredictForm() {
  const dataStr = sessionStorage.getItem('pendingTicketData');
  if(dataStr) {
    const data = JSON.parse(dataStr);
    
    const setVal = (id, val) => { 
      const el = document.getElementById(id); 
      if(el && val !== undefined) el.value = val; 
    };

    setVal('title', data.title);
    setVal('description', data.description);
    setVal('issue_type', data.issue_type);
    setVal('customer_type', data.customer_type);
    setVal('channel', data.channel);
    setVal('impact_level', data.impact_level);
    setVal('previous_complaints', data.previous_complaints);
    setVal('hours_open', data.hours_open);

    // Trigger character count update
    const desc = document.getElementById('description');
    if(desc) {
      desc.dispatchEvent(new Event('input'));
    }

    // Clear after filling
    sessionStorage.removeItem('pendingTicketData');
    
    // Highlight form
    const formObj = document.getElementById('ticketForm');
    if(formObj) {
      formObj.classList.add('glow-highlight');
      setTimeout(() => formObj.classList.remove('glow-highlight'), 2000);
    }
  }
}
