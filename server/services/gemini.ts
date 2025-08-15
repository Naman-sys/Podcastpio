import { GoogleGenAI } from "@google/genai";
import * as cheerio from "cheerio";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });

interface PodcastScriptOptions {
  content: string;
  style: string;
  duration: string;
  showName?: string;
}

interface GeneratedScript {
  intro: string;
  mainContent: string;
  outro: string;
  showNotes: {
    keyTopics: string[];
    resources: string[];
    timestamps: { time: string; topic: string }[];
    episodeDetails: {
      duration: string;
      category: string;
      season?: string;
      episode?: string;
      format: string;
    };
  };
}

export async function generatePodcastScript(options: PodcastScriptOptions): Promise<GeneratedScript> {
  const { content, style, duration, showName } = options;
  
  const systemPrompt = `You are a professional podcast script writer. Create an engaging, well-structured podcast script based on the provided content. 

Style: ${style}
Target Duration: ${duration} minutes
Show Name: ${showName || "The Show"}

The script should include:
1. A compelling intro that hooks the audience
2. Well-structured main content with natural transitions
3. A strong outro with call-to-action
4. Comprehensive show notes

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

Make the script conversational, engaging, and professional. Include music cues like [INTRO MUSIC FADES IN] and [TRANSITION MUSIC]. Ensure natural flow between segments.`;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-pro",
      config: {
        systemInstruction: systemPrompt,
        responseMimeType: "application/json",
        responseSchema: {
          type: "object",
          properties: {
            intro: { type: "string" },
            mainContent: { type: "string" },
            outro: { type: "string" },
            showNotes: {
              type: "object",
              properties: {
                keyTopics: {
                  type: "array",
                  items: { type: "string" }
                },
                resources: {
                  type: "array",
                  items: { type: "string" }
                },
                timestamps: {
                  type: "array",
                  items: {
                    type: "object",
                    properties: {
                      time: { type: "string" },
                      topic: { type: "string" }
                    },
                    required: ["time", "topic"]
                  }
                },
                episodeDetails: {
                  type: "object",
                  properties: {
                    duration: { type: "string" },
                    category: { type: "string" },
                    season: { type: "string" },
                    episode: { type: "string" },
                    format: { type: "string" }
                  },
                  required: ["duration", "category", "format"]
                }
              },
              required: ["keyTopics", "resources", "timestamps", "episodeDetails"]
            }
          },
          required: ["intro", "mainContent", "outro", "showNotes"]
        },
      },
      contents: content,
    });

    const rawJson = response.text;
    if (!rawJson) {
      throw new Error("Empty response from Gemini API");
    }

    const script: GeneratedScript = JSON.parse(rawJson);
    return script;
  } catch (error) {
    console.error("Error generating script with Gemini:", error);
    throw new Error(`Failed to generate podcast script: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}

export interface FetchedContent {
  title: string;
  content: string;
  wordCount: number;
}

export async function fetchContentFromUrl(url: string): Promise<FetchedContent> {
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch content: ${response.status} ${response.statusText}`);
    }
    
    const html = await response.text();
    const $ = cheerio.load(html);
    
    // Remove script and style elements
    $('script, style, nav, footer, aside, .nav, .footer, .sidebar').remove();
    
    // Try to find the main content area
    let content = '';
    let title = '';
    
    // Extract title
    title = $('title').text() || $('h1').first().text() || 'Untitled Article';
    
    // Try different selectors for main content
    const contentSelectors = [
      'article',
      'main',
      '.content',
      '.article-content',
      '.post-content',
      '.entry-content',
      '#content',
      '.story-body',
      '.article-body'
    ];
    
    for (const selector of contentSelectors) {
      const element = $(selector);
      if (element.length && element.text().trim().length > 100) {
        content = element.text().trim();
        break;
      }
    }
    
    // Fallback to body content if no specific content area found
    if (!content) {
      content = $('body').text().trim();
    }
    
    // Clean up the content
    content = content
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .replace(/\n\s*\n/g, '\n\n') // Clean up line breaks
      .trim();
    
    if (content.length < 50) {
      throw new Error("Could not extract meaningful content from the URL");
    }
    
    const wordCount = content.trim().split(/\s+/).length;
    
    return {
      title: title.trim(),
      content,
      wordCount
    };
  } catch (error) {
    console.error("Error fetching content from URL:", error);
    throw new Error(`Failed to fetch content from URL: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}
