const MAX_NUM_GUESSES = window.league === "pwhl" ? 6 : 8; // Fewer guesses for PWHL due to smaller player pool

// Create a sharable text representation of the game result
export function createSharable(numGuesses, rowsToShow = numGuesses) {

    // Show daily number only in daily mode
    const dailyLabel = window.gameMode === "daily" ? `#${window.dailyGameNumber}` : "";

    // First lines of sharable text
    let sharable = `PuckGuessr ${dailyLabel} 🏒 - ${numGuesses}/${MAX_NUM_GUESSES}\n\n`;

    // If the player lost without forfeiting, show all rows
    if (rowsToShow === "X") {
        rowsToShow = MAX_NUM_GUESSES;
    }

    // Cycle through player info boxes and create a string of emojis based on colour of boxes
    for (let i = 1; i <= rowsToShow; i++) {
        var rowBoxes = document.getElementsByClassName(`player-info-${i}`);
        var rowBoxesArray = Array.from(rowBoxes);
        
        rowBoxesArray.forEach((box) => {
            if (box.style.backgroundColor === "rgb(83, 141, 78)") {
                sharable += "🟩";
            } else if (box.style.backgroundColor === "rgb(181, 159, 59)") {
                sharable += "🟨";
            } else {
                sharable += "⬛";
            }
        });

        // Separate rows of boxes
        sharable += "\n";
    }

    // Add challenge message and URL of game
    sharable += "\nThink you know puck? Try beating my score!\n\n" + window.location.href;

    // Replace newlines with <br> for HTML display
    sharable = sharable.replace(/\n/g, '<br>')

    return sharable;
}