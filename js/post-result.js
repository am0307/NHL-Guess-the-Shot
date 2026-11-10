export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Handle API route
    if (url.pathname === "/api/submit-score" && request.method === "POST") {
      try {

        const { playerName, result, league } = await request.json(); // Retrieve game result for player

        if (!playerName || !result) { // Handle missing information
          return new Response("Missing playerName or result", { status: 400 });
        }

        // Retrieve player data file for the respective league, defaulting to NHL
        const fileKey = league === "pwhl" ? "pwhl_player_data.json" : "player_data.json";
        const object = await env.MY_BUCKET.get(fileKey);
        
        if (!object) {
          return new Response("Game data file not found", { status: 404 });
        }
        
        const gameData = await object.json();

        // If player DNE
        if (!gameData.players[playerName]) {
          return new Response("Player not found", { status: 404 });
        }

        // Initialise results if missing from player, with fewer guesses for PWHL
        if (!gameData.players[playerName].results) {
          const maxGuesses = league === "pwhl" ? 6 : 8;
          const newResults = {};

          for (let i = 1; i <= maxGuesses; i++) {
            newResults[String(i)] = 0;
          }
          newResults["X"] = 0;
          newResults["total_guesses"] = 0;

          gameData.players[playerName].results = newResults;
        }

        // Increment result stats
        const playerResults = gameData.players[playerName].results;
        if (playerResults[result] !== undefined) {
          playerResults[result] += 1;
        }
        playerResults.total_guesses += 1;

        // Save back to R2
        await env.MY_BUCKET.put(fileKey, JSON.stringify(gameData, null, 4), {
          httpMetadata: { 
            contentType: "application/json",
            cacheControl: "no-store, no-cache, must-revalidate"
          },
        });

        return new Response(JSON.stringify({ success: true, results: playerResults }), {
          headers: { "Content-Type": "application/json" },
        });

      } catch (error) { // Error handling
        return new Response(JSON.stringify({ error: error.message }), { 
          status: 500, 
          headers: { "Content-Type": "application/json" } 
        });
      }
    }

    // Static files fallback
    return env.ASSETS.fetch(request);
  },

  // Trigger daily update at midnight Eastern time
  async scheduled(controller, env, ctx) {

    // Get hour in New York to account for daylight saving time
    const easternHour = new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      hour: "numeric",
      hourCycle: "h23"
    }).format(new Date(controller.scheduledTime));

    if (Number(easternHour) !== 0) { // Only continue for the trigger that lands on midnight
      return;
    }

    // Send POST request to start GitHub workflow
    const response = await fetch("https://api.github.com/repos/am0307/NHL-Guess-the-Shot/actions/workflows/daily_update.yml/dispatches", {
      method: "POST",
      headers: {
        "Accept": "application/vnd.github+json",
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "User-Agent": "PuckGuessr Daily Update",
        "X-GitHub-Api-Version": "2022-11-28"
      },
      body: JSON.stringify({ ref: "main" })
    });

    if (!response.ok) { // Error handling
      throw new Error(`Failed to start daily update: ${response.status} ${await response.text()}`);
    }
  },
};