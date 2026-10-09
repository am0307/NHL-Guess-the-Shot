const MAX_NUM_GUESSES = 6;

// Create a sharable text representation of the game result
export function createSharable(numGuesses) {

    // First lines of sharable text
    let sharable = "PuckGuessr - " + numGuesses + "/" + MAX_NUM_GUESSES + "\n\n";

    // If the player lost, set numGuesses to 6 for the purpose of creating the sharable text
    if (numGuesses === "X") {
        numGuesses = 6;
    }
    
    // Cycle through player info boxes and create a string of emojis based on colour of boxes
    for (let i = 1; i <= numGuesses; i++) {
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

    // URL of game
    sharable += "\n" + window.location.href;

    // Replace newlines with <br> for HTML display
    sharable = sharable.replace(/\n/g, '<br>')

    return sharable;
}