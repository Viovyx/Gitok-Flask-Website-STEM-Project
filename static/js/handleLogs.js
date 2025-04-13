var page;
var shown;
var typeSelection;
var userSelection;

var pageSelector = document.getElementById("page-selector");
var shownSelector = document.getElementById("shown-selector");
var typeSelector = document.getElementById("type-selector");
var userSelector = document.getElementById("user-selector");

pageSelector.addEventListener("change", update);
shownSelector.addEventListener("change", update);
typeSelector.addEventListener("change", update);
userSelector.addEventListener("change", update);

function update() {
    page = pageSelector.value;
    shown = shownSelector.value;
    typeSelection = typeSelector.selectedOptions[0].value;
    userSelection = userSelector.selectedOptions[0].value;

    window.location.replace(`/log?page=${page}&shown=${shown}&type="${typeSelection}"&user="${userSelection}"`);
}
