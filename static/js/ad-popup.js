(function () {
  var POPUP_ID = "ad-popup";
  var STORAGE_KEY = "adPopupDismissedUntil";
  var SHOW_DELAY_MS = 1500;      // wait a moment before showing, so it doesn't feel like a jump-scare
  var RESHOW_AFTER_MS = 24 * 60 * 60 * 1000; // reappear once a day after being dismissed

  function dismissedRecently() {
    var until = localStorage.getItem(STORAGE_KEY);
    if (!until) return false;
    return Date.now() < parseInt(until, 10);
  }

  function markDismissed() {
    localStorage.setItem(STORAGE_KEY, String(Date.now() + RESHOW_AFTER_MS));
  }

  document.addEventListener("DOMContentLoaded", function () {
    var popup = document.getElementById(POPUP_ID);
    var closeBtn = document.getElementById("ad-popup-close");
    if (!popup || !closeBtn) return;

    if (dismissedRecently()) return;

    setTimeout(function () {
      popup.classList.add("show");
    }, SHOW_DELAY_MS);

    closeBtn.addEventListener("click", function () {
      popup.classList.remove("show");
      markDismissed();
    });
  });
})();