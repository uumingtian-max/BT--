// BKLT Clean Home helper
// On the empty clean landing page, automatically select Agent mode so the user
// can just type a task. Tools/skills stay hidden unless execution emits steps.
(function () {
  function textOf(el) {
    return (el && el.textContent ? el.textContent : '').replace(/\s+/g, ' ').trim();
  }

  function hasConversationMessages() {
    return Boolean(document.querySelector('.msg-user, .msg-assistant, .agent-steps-wrap'));
  }

  function isCleanHome() {
    return Boolean(document.querySelector('.dashboard-panel')) && !hasConversationMessages();
  }

  function selectAgentMode() {
    if (!isCleanHome()) return;
    var buttons = Array.from(document.querySelectorAll('button'));
    var agentButton = buttons.find(function (btn) {
      return textOf(btn) === 'Agent' || /\bAgent\b/.test(textOf(btn));
    });
    if (agentButton && !agentButton.classList.contains('active')) {
      agentButton.click();
    }
  }

  function focusComposer() {
    if (!isCleanHome()) return;
    var textarea = document.querySelector('.input-box textarea');
    if (textarea && document.activeElement !== textarea) {
      textarea.focus({ preventScroll: true });
    }
  }

  function tick() {
    selectAgentMode();
    focusComposer();
  }

  window.addEventListener('DOMContentLoaded', function () {
    tick();
    var observer = new MutationObserver(function () {
      window.requestAnimationFrame(tick);
    });
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    window.setInterval(tick, 2000);
  });
})();
