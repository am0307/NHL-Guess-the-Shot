export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Handle API route
    if (url.pathname === "/api/submit-score" && request.method === "POST") {
      try {

        const { playerName, result } = await request.json(); // Retrieve game result for player
        
        if (!playerName || !result) { // Handle missing information
          return new Response("Missing playerName or result", { status: 400 });
        }

        // Retrieve player_data file
        const fileKey = "player_data.json";
        const object = await env.MY_BUCKET.get(fileKey);
        
        if (!object) {
          return new Response("Game data file not found", { status: 404 });
        }
        
        const gameData = await object.json();

        // If player DNE
        if (!gameData.players[playerName]) {
          return new Response("Player not found", { status: 404 });
        }

        // Initialise results if missing from player
        if (!gameData.players[playerName].results) {
          gameData.players[playerName].results = {
            "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "X": 0, "total_guesses": 0
          };
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
};