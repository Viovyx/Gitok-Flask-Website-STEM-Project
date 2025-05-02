var mode = localStorage.getItem("mode");

if (mode == null) {
    localStorage.setItem("mode", "dm");
    mode = "dm";
}

async function setTheme(mode = "lm") {
    const elements = [
        "background",
        "foreground",
        "border",
        "copy",
        "copy-light",
        "copy-lighter",
    ];

    elements.forEach((element) => {
        document.documentElement.style.setProperty(
            `--${element}`,
            `var(--${element}-${mode})`
        );
    });
    localStorage.setItem("mode", mode);
;
    if (mode == "lm") {
        document.getElementById("sun-toggle").classList.add("hidden");
        document.getElementById("moon-toggle").classList.remove("hidden");
    }
    else {
        document.getElementById("sun-toggle").classList.remove("hidden");
        document.getElementById("moon-toggle").classList.add("hidden");
    }
}

function toggleTheme() {
    if (mode == "lm") {
        localStorage.setItem("mode", "dm");
        mode = "dm";
    } else {
        localStorage.setItem("mode", "lm");
        mode = "lm";
    }
    setTheme(mode);
}

setTheme(mode);