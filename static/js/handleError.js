var url = new URL(window.location.href);
var error = url.searchParams.get("error");
if (error) {
    const errorMessage = document.getElementById("error-message");
    errorMessage.classList.remove("hidden");

    switch (error) {
        case "bad_login":
            errorMessage.textContent =
                "Wrong email or password. Please try again.";
            break;
        case "bad_pass":
            errorMessage.textContent = "Wrong password. Please try again.";
            break;
        case "match_pass":
            errorMessage.textContent =
                "New & Confirm passwords do not match. Please try again.";
            break;
        case "invalid_field":
            errorMessage.textContent =
                "Invalid content for one or more fields. Please try again.";
            break;
        case "duplicate_key":
            errorMessage.textContent =
                "A value already exists. Please try again.";
            break;
        case "no_admin":
            errorMessage.textContent =
                "Only admins are allowed to log in to the webpanel.";
            break;
        default:
            errorMessage.classList.add("hidden");
            alert(`An error occurred without an error message (${error}). `);
    }

    let url = new URL(window.location.href);
    url.searchParams.delete("error");
    history.replaceState(history.state, "", url.href);
}
