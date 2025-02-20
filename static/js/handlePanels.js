const editPanel = document.getElementById('edit-panel');
const createPanel = document.getElementById('create-panel');

function openPanel(type) {
    switch (type) {
        case 'edit':
            editPanel.classList.remove('hidden');
            break;
        case 'create':
            createPanel.classList.remove('hidden');
            break;
        default:
            console.error('Invalid panel type:', type);
    }
}

function closePanel(type) {
    switch (type) {
        case 'edit':
            editPanel.classList.add('hidden');
            break;
        case 'create':
            createPanel.classList.add('hidden');
            break;
        default:
            console.error('Invalid panel type:', type);
    }
}

function deleteItem() {
    const confirmed = confirm('Are you sure you want to delete this item?');
    if (confirmed) {
        closePanel('edit');
    }
}