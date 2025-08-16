import type { Handler, HandlerEvent, HandlerContext } from "@netlify/functions";

// Use dynamic import for Google AI to avoid bundling issues
async function getGoogleAI() {
  const { GoogleGenerativeAI } = await import("@google/generative-ai");
  return GoogleGenerativeAI;
}

const handler: Handler = async (event: HandlerEvent, context: HandlerContext) => {
  // Set CORS headers
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  };

  // Handle preflight requests
  if (event.httpMethod === "OPTIONS") {
    return {
      statusCode: 200,
      headers,
      body: "",
    };
  }

  try {
    const path = event.path.replace("/.netlify/functions/api", "");
    
    // Route: POST /scripts/generate
    if (path === "/scripts/generate" && event.httpMethod === "POST") {
      const body = JSON.parse(event.body || "{}");
      const { content, style, duration, showName } = body;

      if (!content) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: "Content is required" }),
        };
      }

      // Initialize Gemini AI
      const apiKey = process.env.GEMINI_API_KEY;
      if (!apiKey) {
        return {
          statusCode: 500,
          headers,
          body: JSON.stringify({ error: "Gemini API key not configured" }),
        };
      }

      const GoogleGenerativeAI = await getGoogleAI();
      const genAI = new GoogleGenerativeAI(apiKey);
      const model = genAI.getGenerativeModel({ model: "gemini-pro" });

      const prompt = `You are a professional podcast script writer. Create an engaging, well-structured podcast script based on the provided content.

Style: ${style || "conversational"}
Target Duration: ${duration || "10-20"} minutes
Show Name: ${showName || "The Show"}

The script should include:
1. A compelling intro that hooks the audience
2. Well-structured main content with natural transitions
3. A strong outro with call-to-action
4. Comprehensive show notes

Content to convert:
${content}

Format the response as JSON with this exact structure:
{
  "intro": "Complete intro segment with host dialogue and music cues",
  "mainContent": "Main content with segments and transitions",
  "outro": "Outro segment with wrap-up and next episode teaser",
  "showNotes": {
    "keyTopics": ["topic1", "topic2"],
    "resources": ["resource1", "resource2"],
    "timestamps": [{"time": "0:00", "topic": "Introduction"}],
    "episodeDetails": {
      "duration": "~20 minutes",
      "category": "Technology",
      "format": "Solo Commentary"
    }
  }
}

Make the script conversational, engaging, and professional. Include music cues like [INTRO MUSIC FADES IN] and [TRANSITION MUSIC].`;

      const result = await model.generateContent(prompt);
      const response = await result.response;
      const text = response.text();

      // Extract JSON from response
      const jsonStart = text.indexOf('{');
      const jsonEnd = text.lastIndexOf('}') + 1;
      
      if (jsonStart !== -1 && jsonEnd > jsonStart) {
        const jsonText = text.slice(jsonStart, jsonEnd);
        const scriptData = JSON.parse(jsonText);
        
        return {
          statusCode: 200,
          headers,
          body: JSON.stringify(scriptData),
        };
      } else {
        throw new Error("Failed to parse AI response");
      }
    }

    // Route not found
    return {
      statusCode: 404,
      headers,
      body: JSON.stringify({ error: "Route not found" }),
    };

  } catch (error) {
    console.error("Function error:", error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ 
        error: "Internal server error",
        message: error instanceof Error ? error.message : "Unknown error"
      }),
    };
  }
};

export { handler };