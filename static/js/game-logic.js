// Retrieve elements, variables, and functions
const input = document.getElementById("player-input");
const dropdown = document.getElementById("player-dropdown");
const form = document.getElementById("player-form");
const items = dropdown.querySelectorAll(".player-option");
const tooltips = document.querySelectorAll(".column-tooltip");
import { createSharable } from "./share-logic.js";

let guessCount = 0; // Guess number tracker

// Create Bootstrap tooltips
tooltips.forEach(tt => {
    new bootstrap.Tooltip(tt)
})

// Show and filter dropdown as the user types
input.addEventListener("input", function() {
    const user_input = input.value.toLowerCase();
    const max_displayed = 5;
    let num_displayed = 0;
    let hasVisibleItems = false;

    // Loop through each item and show players based on the filter
    items.forEach(item => {
        var player_text = item.textContent.toLowerCase();
        const player_text_deaccent = player_text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const user_input_deaccent = user_input.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        
        if (player_text_deaccent.includes(user_input_deaccent) && user_input_deaccent.length > 0 && num_displayed < max_displayed) {
            item.parentElement.style.display = "block";
            hasVisibleItems = true;
            num_displayed++;
        } else {
            item.parentElement.style.display = "none";
        }
    });

    dropdown.style.display = (hasVisibleItems && user_input.length > 0) ? "block" : "none";
});

// Handle click on a list item
items.forEach(item => {
    item.addEventListener("click", function(e) {
        e.preventDefault();

        const playerName = this.getAttribute("data-value");
        input.value = playerName;
        dropdown.style.display = "none";
        
        guessCount++;
        addGuessInfo(playerName);
        
        input.value = "";
        flipBoxes(playerName);
    });
});

// Hide dropdown on outside click
document.addEventListener("click", function(e) {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = "none";
    }
});

// Prevent submission by entering
form.addEventListener("keydown", function(e) {
    if (e.key === "Enter") {
        e.preventDefault();
    }
});

// Make boxes flip
function flipBoxes(playerName) {
    var boxes = document.getElementsByClassName(`player-info-${guessCount}`);
    var boxArray = Array.from(boxes);
    boxArray.map(function (box, i) {
        box.classList.add("flip");
        box.style.animationDelay = `${i * 250}ms`;

        setTimeout(() => {
            colourBox(box, i, playerName);
        }, (i * 250) + 250);

        setTimeout(() => {
            displayAnswer(playerName)
        }, (5 * 250) + 250);
    });
}

// Display answer on correct guess/loss
function displayAnswer(playerName) {
    if (playerName === window.answerName) { // Win
        const successAlert = document.getElementById("win-alert");
        const maskVideo = document.getElementById("mask-vid");
        const originalVideo = document.getElementById("org-vid");

        successAlert.classList.remove("d-none");
        originalVideo.classList.remove("d-none");
        form.classList.add("d-none");
        maskVideo.classList.add("d-none");
        
        // Create and show sharable text for a win
        if (window.location.pathname === "/") {
            const sharable = createSharable(guessCount);
            document.querySelector("#shareResultWin .modal-body").innerHTML = sharable;
        }
    } else if (guessCount == 6) { // Loss
        const lossAlert = document.getElementById("loss-alert");
        const maskVideo = document.getElementById("mask-vid");
        const originalVideo = document.getElementById("org-vid");

        lossAlert.classList.remove("d-none");
        originalVideo.classList.remove("d-none");
        form.classList.add("d-none");
        maskVideo.classList.add("d-none");

        // Create and show sharable text for a loss
        if (window.location.pathname === "/") {
            const sharable = createSharable("X");
            document.querySelector("#shareResultLoss .modal-body").innerHTML = sharable;
        }
    }
}

// Colour boxes based on the guessed player's info
function colourBox(box, index, playerName) {
    const player_info = window.playerData[playerName];

    switch (index) {
        case 0:
            if (player_info.team === window.answerInfo.team) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else {
                box.style.backgroundColor = "#3A3A3C";
                box.style.color = "white";
            }
            break;
        case 1:
            if (player_info.division === window.answerInfo.division) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else if (player_info.conference === window.answerInfo.conference) {
                box.style.backgroundColor = "#B59F3B"; 
                box.style.color = "white";
            } else {
                box.style.backgroundColor = "#3A3A3C";
                box.style.color = "white";
            }
            break;
        case 2:
            if (player_info.number === window.answerInfo.number) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else if (Math.abs(player_info.number - window.answerInfo.number) <= 10) {
                box.style.backgroundColor = "#B59F3B"; 
                box.style.color = "white";
            } else {
                box.style.backgroundColor = "#3A3A3C";
                box.style.color = "white";
            }
            break;
        case 3:
            if (player_info.nation === window.answerInfo.nation) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else {
                box.style.backgroundColor = "#3A3A3C";
                box.style.color = "white";
            }
            break;
        case 4:
            if (player_info.age === window.answerInfo.age) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else if (Math.abs(player_info.age - window.answerInfo.age) <= 3) {
                box.style.backgroundColor = "#B59F3B"; 
                box.style.color = "white";
            } else {
                box.style.backgroundColor = "#3A3A3C";
                box.style.color = "white";
            }
            break;
    }
}

// Add guess info to the next row of boxes
function addGuessInfo(playerName) {
    const guessRow = document.getElementById(`guess-${guessCount}`);
    const team = guessRow.querySelector(".team");
    const division = guessRow.querySelector(".division");
    const number = guessRow.querySelector(".number");
    const nation = guessRow.querySelector(".nation");
    const age = guessRow.querySelector(".age");

    const player_info = window.playerData[playerName];
    if (player_info) {
        team.innerText = player_info.team;
        division.innerText = player_info.division;
        number.innerText = player_info.number;
        nation.innerText = player_info.nation;
        age.innerText = player_info.age;
    }

    if (guessCount >= 6) return;
}

// Handle copy from win modal
const copyWinBtn = document.getElementById("copy-win-btn");
if (copyWinBtn) { // Check if button exists prior to adding event listener

    // Copy text on click
    copyWinBtn.addEventListener("click", function() {
        const textToCopy = document.querySelector("#shareResultWin .modal-body").textContent;
        
        // Change button text to "Copied!" for 2 seconds
        navigator.clipboard.writeText(textToCopy).then(() => {
            copyWinBtn.textContent = "Copied!";
            setTimeout(() => {
                copyWinBtn.textContent = "Copy";
            }, 2000); 
        })
    });
}

// Handle copy from loss modal
const copyLossBtn = document.getElementById("copy-loss-btn");
if (copyLossBtn) { // Check if button exists prior to adding event listener

    // Copy text on click
    copyLossBtn.addEventListener("click", function() {
        const textToCopy = document.querySelector("#shareResultLoss .modal-body").textContent;
        
        // Change button text to "Copied!" for 2 seconds
        navigator.clipboard.writeText(textToCopy).then(() => {
            copyLossBtn.textContent = "Copied!";
            setTimeout(() => {
                copyLossBtn.textContent = "Copy";
            }, 2000);
        })
    });
}