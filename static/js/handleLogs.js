var pageSelector = document.getElementById("page-selector")
var ppSelector = document.getElementById("pp-selector")

pageSelector.addEventListener('change', postUpdate);
ppSelector.addEventListener('change', postUpdate);

function postUpdate(){
    const page = pageSelector.value;
    const pp = ppSelector.value;

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/log';

    const pageInput = document.createElement('input');
    pageInput.type = 'hidden';
    pageInput.name = 'page';
    pageInput.value = page;

    const ppInput = document.createElement('input');
    ppInput.type = 'hidden';
    ppInput.name = 'pp';
    ppInput.value = pp;

    form.appendChild(pageInput);
    form.appendChild(ppInput);

    document.body.appendChild(form);
    form.submit();
}