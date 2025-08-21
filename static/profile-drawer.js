// Global Profile Drawer (slider) for Toolflock
// Attaches to #profileBtn if present and replaces any dropdown with a right-side drawer

(function () {
  function createDrawer(initialText) {
    const overlay = document.createElement('div');
    overlay.id = 'profileDrawerOverlay';
    overlay.className = 'drawer-overlay';
    overlay.innerHTML = `
      <div class="drawer" id="profileDrawer" role="dialog" aria-modal="true">
        <div class="drawer-header">
          <div class="drawer-avatar">${(initialText || 'U').toUpperCase().slice(0,1)}</div>
          <div class="drawer-title">Your Account</div>
          <button class="drawer-close" id="drawerClose" aria-label="Close">✕</button>
        </div>
        <div class="drawer-content">
          <a class="drawer-link" href="/profile">Profile</a>
          <a class="drawer-link" href="/all-tools">All Tools</a>
          <a class="drawer-link" href="/privacy">Privacy Policy</a>
          <a class="drawer-link" href="/terms">Terms of Service</a>
        </div>
        <div class="drawer-footer">
          <a class="drawer-signout" href="/signout">Sign Out</a>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    const close = () => overlay.classList.remove('open');
    const open = () => overlay.classList.add('open');

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) close();
    });
    overlay.querySelector('#drawerClose').addEventListener('click', close);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close();
    });

    return { open, close, overlay };
  }

  function init() {
    const profileBtn = document.getElementById('profileBtn');
    if (!profileBtn) return;

    // Read initial from data attribute or fallback to hidden avatar text
    const initialAttr = profileBtn.getAttribute('data-initial');
    const avatar = profileBtn.querySelector('.profile-avatar');
    const initialText = (initialAttr && initialAttr.trim()) || (avatar ? (avatar.textContent || 'U').trim() : 'U');
    const drawer = createDrawer(initialText);

    // Ensure any old dropdown stays hidden
    const dd = document.getElementById('profileDropdown');
    if (dd) dd.style.display = 'none';

    // Intercept click to open drawer
    profileBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      drawer.open();
    }, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();


