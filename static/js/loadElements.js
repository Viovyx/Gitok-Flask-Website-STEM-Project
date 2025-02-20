var elements = ["header", "footer", "sun-toggle", "moon-toggle", "edit-panel", "create-panel"];

elements.forEach((elementId) => {
    var element = document.getElementById(elementId);
    if (element) {
        fetch("/get_element/" + elementId)
            .then((response) => response.text())
            .then((data) => {
                var html_content = data;
                element.innerHTML = html_content;
            })
            .catch((error) =>
                console.error("Error loading " + elementId + ":", error)
            );
    }
});
