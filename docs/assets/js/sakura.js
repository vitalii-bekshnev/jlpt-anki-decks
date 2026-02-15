// Sakura petal animation for Japanese VN aesthetic

// Language switching functionality
const LanguageManager = {
  currentLang: null,
  
  init() {
    this.currentLang = this.detectLanguage();
    this.setupLanguageSwitcher();
  },
  
  detectLanguage() {
    // Check URL path first
    const path = window.location.pathname;
    if (path.includes('/ru/')) return 'ru';
    if (path.includes('/en/')) return 'en';
    
    // Check stored preference
    const stored = localStorage.getItem('preferred-language');
    if (stored) return stored;
    
    // Detect from browser
    const browserLang = navigator.language || navigator.userLanguage;
    if (browserLang.startsWith('ru')) return 'ru';
    
    return 'en';
  },
  
  setupLanguageSwitcher() {
    // Update language switcher active state
    document.querySelectorAll('.lang-switcher a').forEach(link => {
      link.addEventListener('click', (e) => {
        const lang = link.getAttribute('href').includes('/ru/') ? 'ru' : 'en';
        localStorage.setItem('preferred-language', lang);
      });
    });
  },
  
  switchTo(lang) {
    const currentPath = window.location.pathname;
    const currentPage = currentPath.split('/').pop() || 'index.html';
    
    // If we're on root, redirect to appropriate language folder
    if (!currentPath.includes('/en/') && !currentPath.includes('/ru/')) {
      window.location.href = `./${lang}/${currentPage}`;
      return;
    }
    
    // Switch between languages
    let newPath;
    if (lang === 'ru') {
      newPath = currentPath.replace('/en/', '/ru/');
    } else {
      newPath = currentPath.replace('/ru/', '/en/');
    }
    
    if (newPath !== currentPath) {
      window.location.href = newPath;
    }
  }
};

document.addEventListener('DOMContentLoaded', function() {
  // Initialize language manager
  LanguageManager.init();
  
  const container = document.createElement('div');
  container.className = 'sakura-container';
  document.body.insertBefore(container, document.body.firstChild);

  const petalCount = 15;
  const petals = [];

  function createPetal() {
    const petal = document.createElement('div');
    petal.className = 'sakura-petal';
    
    // Randomize petal properties
    const size = Math.random() * 10 + 10;
    const left = Math.random() * 100;
    const duration = Math.random() * 10 + 10;
    const delay = Math.random() * 10;
    
    petal.style.width = `${size}px`;
    petal.style.height = `${size}px`;
    petal.style.left = `${left}%`;
    petal.style.animationDuration = `${duration}s`;
    petal.style.animationDelay = `${delay}s`;
    
    // Randomize opacity
    petal.style.opacity = Math.random() * 0.4 + 0.3;
    
    container.appendChild(petal);
    
    // Remove and recreate petal after animation
    setTimeout(() => {
      if (petal.parentNode) {
        petal.remove();
        createPetal();
      }
    }, (duration + delay) * 1000);
  }

  // Create initial petals
  for (let i = 0; i < petalCount; i++) {
    setTimeout(() => createPetal(), i * 500);
  }

  // Smooth scroll for navigation links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Add hover effect to cards
  document.querySelectorAll('.feature-card, .release-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-5px)';
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });
});
