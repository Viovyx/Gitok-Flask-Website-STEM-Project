var url = new URL(window.location.href);
var error = url.searchParams.get("error");
if (error) {
    const errorMessage = document.getElementById('error-message');
    errorMessage.classList.remove('hidden');

    switch (error) {
        case "bad_login":
            errorMessage.textContent = "Invalid email or password. Please try again.";
            break;
        case "bad_pass":
            errorMessage.textContent = "Wrong password. Please try again."
            break;
        case "match_pass":
            errorMessage.textContent = "New & Confirm passwords do not match. Please try again."
            break;
        default:
            alert("An error occurred. Please try again later.");
    }

    let url = new URL(window.location.href);
    url.searchParams.delete("error");
	history.replaceState(history.state, '', url.href);
}