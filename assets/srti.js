(function () {
    "use strict";

    var state = document.querySelector("[data-collected-at]");
    if (state) {
        var collected = new Date(state.dataset.collectedAt);
        var ageHours = (Date.now() - collected.getTime()) / 3600000;
        var label = state.querySelector("[data-snapshot-label]");
        if (Number.isFinite(ageHours)) {
            var stateName = "recent";
            var stateText = "RECENT SNAPSHOT";
            if (ageHours > 24) {
                stateName = "stale";
                stateText = "STALE SNAPSHOT";
            } else if (ageHours > 6) {
                stateName = "aging";
                stateText = "AGING SNAPSHOT";
            }
            state.dataset.state = stateName;
            label.textContent = stateText + " · " + Math.max(0, Math.floor(ageHours)) + "H OLD";
        }
    }

    var filters = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
    var events = Array.prototype.slice.call(document.querySelectorAll("[data-regions]"));
    var empty = document.querySelector("[data-filter-empty]");

    filters.forEach(function (button) {
        button.addEventListener("click", function () {
            var selected = button.dataset.filter;
            var visible = 0;
            filters.forEach(function (candidate) {
                candidate.setAttribute("aria-pressed", String(candidate === button));
            });
            events.forEach(function (event) {
                var regions = event.dataset.regions.split(" ");
                var show = selected === "all" || regions.indexOf(selected) !== -1;
                event.hidden = !show;
                if (show) visible += 1;
            });
            if (empty) empty.hidden = visible !== 0;
        });
    });
}());
