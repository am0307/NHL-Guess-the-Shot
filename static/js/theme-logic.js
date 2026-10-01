let darkmode = localStorage.getItem("darkmode");
const themeSwitch = document.getElementById("theme-switch");

// Set dark mode
const enableDarkmode = () => {
    document.documentElement.setAttribute("data-bs-theme", "dark");
    localStorage.setItem("darkmode", "active");
};

// Set light mode
const enableLightmode = () => {
    document.documentElement.setAttribute("data-bs-theme", "light");
    localStorage.setItem("darkmode", "inactive");
};

// Apply dark mode if it was previously switched on by the user
if (darkmode === "active") {
    enableDarkmode();
}

// Make theme toggle clickable
if (themeSwitch) {
    themeSwitch.addEventListener("click", () => {
        const websiteTheme = document.documentElement.getAttribute("data-bs-theme");
        websiteTheme !== "dark" ? enableDarkmode() : enableLightmode();
    });
}