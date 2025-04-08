var pageSelector = document.getElementById("page-selector")
var ppSelector = document.getElementById("pp-selector")

pageSelector.addEventListener('change', postUpdate);
ppSelector.addEventListener('change', postUpdate);

function postUpdate(){
    const page = pageSelector.value;
    const pp = ppSelector.value;

    // Create a form dynamically
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/log';

    // Add hidden input fields for the variables
    const pageInput = document.createElement('input');
    pageInput.type = 'hidden';
    pageInput.name = 'page';
    pageInput.value = page;

    const ppInput = document.createElement('input');
    ppInput.type = 'hidden';
    ppInput.name = 'pp';
    ppInput.value = pp;

    // Append inputs to the form
    form.appendChild(pageInput);
    form.appendChild(ppInput);

    // Append the form to the body and submit it
    document.body.appendChild(form);
    form.submit();
}