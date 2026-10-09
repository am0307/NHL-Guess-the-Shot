const nameLookup = {}; // Empty lookup table for player names based on their IDs

// Fetch data from Cloudflare
async function loadGameData() {
    try {
        // Get data
        const response = await fetch(`${window.PUBLIC_R2_URL}/api_cache.json`);
        const data = await response.json();
        
        // Declare variables
        window.playerData = data.players;
        window.videoSources = data.video_sources;

        // Get dropdown element
        const dropdown = document.getElementById("player-dropdown");
        dropdown.innerHTML = ""; // Clear existing

        // Populate the nameLookup and create dropdown options
        for (const [name, data] of Object.entries(window.playerData)) {
            nameLookup[data.id] = name;

            // Create list item for the search dropdown
            const li = document.createElement("li");
            const a = document.createElement("a");
            a.className = "dropdown-item player-option";
            a.href = "#";
            a.setAttribute("data-value", name);
            a.textContent = name;

            // Attach click listener directly to each dynamically created option
            a.addEventListener("click", function(e) {
                e.preventDefault();

                if (guessCount >= 6) { // Only allow submission if user has guesses left
                    return;
                }

                const playerName = this.getAttribute("data-value");
                input.value = playerName;
                dropdown.style.display = "none";
                
                guessCount++;
                addGuessInfo(playerName);
                
                input.value = "";
                flipBoxes(playerName);
            });

            li.appendChild(a);
            dropdown.appendChild(li);
        }

        if (window.gameMode === "daily") {
            // Get daily player
            window.answerId = data.players[data.daily_name].id;
        } else {
            // Check URL for player ID
            const urlParams = new URLSearchParams(window.location.search);
            const requestedId = urlParams.get("id");

            // Retrieve played players
            const playedIds = JSON.parse(localStorage.getItem("played_endless_ids") || "[]").map(String);

            // Validate if the requested ID exists in the nameLookup table
            if (requestedId && nameLookup[requestedId]) {
                window.answerId = requestedId;
            } else {
                // Create an array of all IDs
                const allIds = Object.values(window.playerData).map(p => String(p.id));
                
                // Filter out IDs the user has already played
                let availableIds = allIds.filter(id => !playedIds.includes(id));

                // If all players have been played, empty the played pool to reset the cycle
                if (availableIds.length === 0) {
                    availableIds = allIds;
                    playedIds.length = 0; // Clear memory array
                    localStorage.setItem("played_endless_ids", "[]"); // Clear storage array
                }

                // Pick random from remaining unplayed pool
                const randomId = availableIds[Math.floor(Math.random() * availableIds.length)];
                window.answerId = randomId;

                // Add new ID to URL
                const newUrl = `${window.location.pathname}?id=${window.answerId}`;
                window.history.replaceState({}, '', newUrl);
            }

            // Trigger already played state if applicable
            const currentId = String(window.answerId);
            if (playedIds.includes(currentId)) {
                window.alreadyPlayed = true;
            }

            if (playedIds.includes(currentId)) {
                window.alreadyPlayed = true;
            } else {
                playedIds.push(currentId);
                localStorage.setItem("played_endless_ids", JSON.stringify(playedIds));
            }
        }

        // Set video sources from Cloudflare
        document.getElementById("mask-vid").src = `${window.PUBLIC_R2_URL}/videos/masks/${window.answerId}.mp4`;
        document.getElementById("org-vid").src = `${window.PUBLIC_R2_URL}/videos/original/${window.answerId}.mp4`;

        // If endless mode and already played, trigger the alert screen without updating streak
        if (window.gameMode === "endless" && window.alreadyPlayed) {
            displayAnswer("Played", false);
        }

    } catch (error) {
        console.error("Error loading game data:", error);
    }
}

// Immediately call function
loadGameData()

// Retrieve elements, variables, and functions
const input = document.getElementById("player-input");
const dropdown = document.getElementById("player-dropdown");
const form = document.getElementById("player-form");
const tooltips = document.querySelectorAll(".column-tooltip");
const initiateForfeit = document.getElementById("start-forfeit")
const confirmForfeit = document.getElementById("give-up");
import { createSharable } from "./share-logic.js";

let guessCount = 0; // Guess number tracker

// Create Bootstrap tooltips
tooltips.forEach(tt => {
    new bootstrap.Tooltip(tt)
})

// Show and filter dropdown as the user types
input.addEventListener("input", function() {
    const userInput = input.value.toLowerCase();
    const maxDisplayed = 5;
    let numDisplayed = 0;
    let hasVisibleItems = false;

    // Get current options
    const currentItems = dropdown.querySelectorAll(".player-option");

    // Loop through each item and show players based on the filter
    currentItems.forEach(item => {
        var playerText = item.textContent.toLowerCase();
        const playerTextDeaccent = playerText.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const userInputDeaccent = userInput.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        
        if (playerTextDeaccent.includes(userInputDeaccent) && userInputDeaccent.length > 0 && numDisplayed < maxDisplayed) {
            item.parentElement.style.display = "block";
            hasVisibleItems = true;
            numDisplayed++;
        } else {
            item.parentElement.style.display = "none";
        }
    });

    dropdown.style.display = (hasVisibleItems && userInput.length > 0) ? "block" : "none";
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

// Giving up logic
confirmForfeit.addEventListener("click", function(e) {
    displayAnswer("Loss");
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
    });

    // Display answer after all boxes have flipped
    setTimeout(() => {
        displayAnswer(playerName);
    }, 1500);
}

// Retrieve answer's name
function getPlayerName() {
    return nameLookup[window.answerId];
}

// Display answer on correct guess/loss
function displayAnswer(playerName, updateStreak = true) {
    
    // Variables to track game state
    let gameFinished = false;
    let gameResult = "";

    // Get answer name and source information
    const answerName = getPlayerName();
    const sourceInfo = videoSources[answerName]

    if (playerName === answerName) { // Win

        // Get link, alerts, and videos elements
        const successAlert = document.getElementById("win-alert");
        const winAnswer = document.getElementById("win-answer");
        const maskVideo = document.getElementById("mask-vid");
        const originalVideo = document.getElementById("org-vid");
        const videoSource = document.getElementById("video-source");
        const videoSourceLink = document.getElementById("video-source-link");

        // Adjust styles and show/hide relevant elements
        successAlert.classList.remove("d-none");
        winAnswer.textContent = `The answer was ${answerName}!`;
        originalVideo.classList.remove("d-none");
        originalVideo.style.marginBottom = "4px";
        videoSource.classList.remove("d-none");
        videoSourceLink.textContent = `${sourceInfo.source} on YouTube`
        videoSourceLink.href = sourceInfo.URL
        initiateForfeit.classList.add("d-none");
        form.classList.add("d-none");
        maskVideo.classList.add("d-none");
        
        const sharable = createSharable(guessCount); // Create sharable text for a win

        // Retrieve win alert
        const winModalBody = document.querySelector("#share-result-win .modal-body")
        if (winModalBody) {
            winModalBody.innerHTML = sharable; // Show text for sharing result
        }

        // Set game state variables
        gameFinished = true;
        gameResult = "win";
    } else if (guessCount == 6 || playerName === "Loss"|| playerName === "Played") { // Loss or already played

        // Get link, alerts, and videos elements
        const lossAlert = document.getElementById("loss-alert");
        const lossAnswer = document.getElementById("loss-answer");
        const maskVideo = document.getElementById("mask-vid");
        const originalVideo = document.getElementById("org-vid");
        const videoSource = document.getElementById("video-source");
        const videoSourceLink = document.getElementById("video-source-link");

        // Adjust styles and show/hide relevant elements
        lossAlert.classList.remove("d-none");
        originalVideo.classList.remove("d-none");
        originalVideo.style.marginBottom = "4px";
        videoSource.classList.remove("d-none");
        videoSourceLink.textContent = `${sourceInfo.source} on YouTube`
        videoSourceLink.href = sourceInfo.URL
        initiateForfeit.classList.add("d-none");
        form.classList.add("d-none");
        maskVideo.classList.add("d-none");


        if (playerName === "Played") { // User already played this player
            // Warning for already playing
            lossAlert.classList.remove("alert-danger");
            lossAlert.classList.add("alert-warning"); 
            lossAlert.querySelector("h4").textContent = "You already played this one!";
            lossAnswer.textContent = `The answer was ${answerName}.`;
            
            // Hide the share button
            const shareBtn = lossAlert.querySelector(".share-result-btn");
            if (shareBtn) {
                shareBtn.classList.add("d-none");
            }

            // Display existing endless streak if needed
            if (window.gameMode === "endless") {
                let currentStreak = parseInt(localStorage.getItem("endless_streak")) || 0;
                const streakDisplay = lossAlert.querySelector(".streak-text");
                
                if (streakDisplay) {
                    streakDisplay.innerHTML = `Current Streak: <strong>${currentStreak}</strong>`;
                    streakDisplay.classList.remove("d-none");
                }
            }

            // Set game state variables
            gameFinished = true;
            gameResult = "played";
        } else { // User lost
            lossAnswer.textContent = `The answer was ${answerName}!`; // Display answer

            let sharable; // Create and show sharable text for a loss
            
            // Create sharable based on whether player forfeited or lost traditionally
            if (playerName === "Loss") {
                sharable = createSharable(guessCount);
                sharable = sharable.replace(guessCount, "X"); // Replace guess count with "X" to mark loss
            } else {
                sharable = createSharable("X");
            }
            
            // Retrieve loss alert
            const lossModalBody = document.querySelector("#share-result-loss .modal-body");
            if (lossModalBody) {
                lossModalBody.innerHTML = sharable; // Show text for sharing result
            }

            // Set game state variables
            gameFinished = true;
            gameResult = "loss";
        }
    }

    // Update endless streak logic
    if (gameFinished && window.gameMode === "endless" && updateStreak) {

        // Add players to played players only after a win/loss
        if (gameResult === "win" || gameResult === "loss") {
            const currentPlayedIds = JSON.parse(localStorage.getItem("played_endless_ids") || "[]").map(String);
            const currentId = String(window.answerId);
            if (!currentPlayedIds.includes(currentId)) {
                currentPlayedIds.push(currentId);
                localStorage.setItem("played_endless_ids", JSON.stringify(currentPlayedIds));
            }
        }
        
        // Send POST request to update streak
        if (window.gameMode === "endless") {
            
            let currentStreak = parseInt(localStorage.getItem("endless_streak")) || 0; // Read the current streak
            
            // Update streak accordingly
            if (gameResult === "win") {
                currentStreak += 1;
            } else if (gameResult === "loss") {
                currentStreak = 0;
            }
            
            localStorage.setItem("endless_streak", currentStreak); // Save streak
            
            // Display appropriate alert
            const targetAlert = gameResult === "win" ? document.getElementById("win-alert") : document.getElementById("loss-alert");
            const streakDisplay = targetAlert.querySelector(".streak-text");

            // Update and show streak
            if (streakDisplay) {
                streakDisplay.innerHTML = `Current Streak: <strong>${currentStreak}</strong>`;
                streakDisplay.classList.remove("d-none");
            }
        }
    }
}

// Colour boxes based on the guessed player's info
function colourBox(box, index, playerName) {
    const playerInfo = window.playerData[playerName];
    const answerName = getPlayerName();
    const answerInfo = window.playerData[answerName];

    switch (index) {
        case 0:
            if (playerInfo.team === answerInfo.team) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else {
                box.style.backgroundColor = "#3A3A3C";
                box.style.color = "white";
            }
            break;
        case 1:
            if (playerInfo.division === answerInfo.division) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else if (playerInfo.conference === answerInfo.conference) {
                box.style.backgroundColor = "#B59F3B"; 
                box.style.color = "white";
            } else {
                box.style.backgroundColor = "#3A3A3C";
                box.style.color = "white";
            }
            break;
        case 2:
            if (playerInfo.number === answerInfo.number) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else if (Math.abs(playerInfo.number - answerInfo.number) <= 10) {
                box.style.backgroundColor = "#B59F3B"; 
                box.style.color = "white";
            } else {
                box.style.backgroundColor = "#3A3A3C";
                box.style.color = "white";
            }
            break;
        case 3:
            if (playerInfo.nation === answerInfo.nation) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else {
                box.style.backgroundColor = "#3A3A3C";
                box.style.color = "white";
            }
            break;
        case 4:
            if (playerInfo.age === answerInfo.age) {
                box.style.backgroundColor = "#538D4E"; 
                box.style.color = "white";
            } else if (Math.abs(playerInfo.age - answerInfo.age) <= 3) {
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

    const playerInfo = window.playerData[playerName];
    if (playerInfo) {
        team.innerText = playerInfo.team;
        division.innerText = playerInfo.division;
        number.innerText = playerInfo.number;
        nation.innerText = playerInfo.nation;
        age.innerText = playerInfo.age;
    }

    if (guessCount >= 6) return;
}

// Handle copy from win modal
const copyWinBtn = document.getElementById("copy-win-btn");
if (copyWinBtn) { // Check if button exists prior to adding event listener

    // Copy text on click
    copyWinBtn.addEventListener("click", function() {
        const textToCopy = document.querySelector("#share-result-win .modal-body").innerText;
        
        // Make sharable text that has working line breaks when copied
        const copyableText = textToCopy.replace(/<br>/g, '\n');

        // Change button text to "Copied!" for 2 seconds
        navigator.clipboard.writeText(copyableText).then(() => {
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
        const textToCopy = document.querySelector("#share-result-loss .modal-body").innerText;
        
        // Make sharable text that has working line breaks when copied
        const copyableText = textToCopy.replace(/<br>/g, '\n');

        // Change button text to "Copied!" for 2 seconds
        navigator.clipboard.writeText(copyableText).then(() => {
            copyLossBtn.textContent = "Copied!";
            setTimeout(() => {
                copyLossBtn.textContent = "Copy";
            }, 2000);
        })
    });
}