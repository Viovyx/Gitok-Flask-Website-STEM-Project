var url = new URL(window.location.href);
var error = url.searchParams.get("error");
if (error) {
    const errorMessage = document.getElementById('error-message');
    errorMessage.classList.remove('hidden');

    switch (error) {
        case "bad_login":
            errorMessage.textContent = "Invalid username or password. Please try again.";
            break;
        default:
            alert("An error occurred. Please try again later.");
    }
}