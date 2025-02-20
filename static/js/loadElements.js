var elements = ["header", "footer", "sun-toggle", "moon-toggle", "edit-panel", "create-panel"];

elements.forEach((element) => {
    var element = document.getElementById(element);
    if (element) {
        fetch("/elements/" + element.id + ".html")
            .then((response) => response.text())
            .then((data) => {
                var html_content = data;
                element.innerHTML = html_content;
            })
            .catch((error) =>
                console.error("Error loading " + element.id + ".html:", error)
            );
    }
});
