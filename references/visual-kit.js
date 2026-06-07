window.KUWVisual = {
  getVisualId(fallback = "post-1") {
    const params = new URLSearchParams(window.location.search);
    return params.get("visual") || window.location.hash.replace("#", "") || fallback;
  },

  escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  },

  renderShell(root, visual) {
    const escape = window.KUWVisual.escapeHtml;
    root.innerHTML = `
      <div class="masthead">
        <span class="source-pill">${escape(visual.badge || "Source")}</span>
        <span class="kicker">${escape(visual.kicker || "")}</span>
      </div>
      <h1>${escape(visual.title || "")}</h1>
      ${visual.subtitle ? `<div class="subhead">${escape(visual.subtitle)}</div>` : ""}
      <section class="frame">${typeof visual.render === "function" ? visual.render() : visual.inner || ""}</section>
      ${visual.note ? `<div class="source-note">${escape(visual.note)}</div>` : ""}
    `;
  },
};
