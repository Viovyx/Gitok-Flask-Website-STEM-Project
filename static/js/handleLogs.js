var pageSelector = document.getElementById("page-selector")
var ppSelector = document.getElementById("shown-selector")

pageSelector.addEventListener('change', update);
ppSelector.addEventListener('change', update);

function update(){
    const page = pageSelector.value;
    const shown = ppSelector.value;
    window.location.replace(`/log?page=${page}&shown=${shown}`)
}