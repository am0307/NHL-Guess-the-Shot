export async function onRequest(context) {
    // Fetches the JSON from GitHub Actions directly via Cloudflare R2
    const cacheFile = await context.env.BUCKET.get("api_cache.json");
    
    if (cacheFile === null) {
        return new Response("Cache not found", { status: 404 });
    }
    
    const data = await cacheFile.json();
    return Response.json(data);
}