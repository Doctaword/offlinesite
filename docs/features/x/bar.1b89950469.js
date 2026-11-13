/* Adds the Home / Professional / Process / Direction / Resume bar to the copies of the original pages. */
(function () {
  var home = document.querySelector('meta[name="ofl-home"]'); if (!home) return;
  var site = new URL(home.content, location.href).href, fx = new URL('../', site).href;
  var items = [['Home', site], ['Professional', fx + 'professional/'], ['Process', fx + 'process/'], ['Direction', fx + 'direction/'], ['Resume', fx + 'resume/']];
  var bar = document.createElement('nav'); bar.id = 'fx-bar';
  items.forEach(function (it, i) { var a = document.createElement('a'); a.href = it[1]; a.textContent = it[0]; if (i === 0) a.className = 'on'; bar.appendChild(a); });
  function add() { document.body.appendChild(bar); }
  if (document.body) add(); else document.addEventListener('DOMContentLoaded', add);
})();
