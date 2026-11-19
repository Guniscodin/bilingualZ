/* Keyboard: the whole point is that advancing costs one keypress. */
(function () {
  const BZ = (window.BZ = window.BZ || {});

  function isTyping(node) {
    return node && /^(INPUT|TEXTAREA|SELECT)$/.test(node.tagName);
  }

  function overlayOpen() {
    return document.querySelector(".overlay:not([hidden])");
  }

  document.addEventListener("keydown", (event) => {
    if (isTyping(event.target)) {
      if (event.key === "Escape") event.target.blur();
      return;
    }

    if (overlayOpen()) {
      if (event.key === "Escape") BZ.app.closeAll();
      return;
    }

    if (event.ctrlKey || event.metaKey || event.altKey) return;

    switch (event.key) {
      case "ArrowRight":
      case "ArrowDown":
      case " ":
      case "j":
        event.preventDefault();
        BZ.app.next();
        break;
      case "ArrowLeft":
      case "ArrowUp":
      case "k":
        event.preventDefault();
        BZ.app.prev();
        break;
      case "[":
        event.preventDefault();
        BZ.app.nudge(-1);
        break;
      case "]":
        event.preventDefault();
        BZ.app.nudge(1);
        break;
      case "a":
      case "A":
        event.preventDefault();
        BZ.app.lock();
        break;
      case "f":
      case "F":
        event.preventDefault();
        BZ.app.toggleFocus();
        break;
      case "n":
      case "N":
        event.preventDefault();
        BZ.app.openNew();
        break;
      case "Home":
        event.preventDefault();
        BZ.app.first();
        break;
      case "End":
        event.preventDefault();
        BZ.app.last();
        break;
      default:
        break;
    }
  });
})();
