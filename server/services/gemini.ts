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

function generateFallbackScript(options: PodcastScriptOptions): GeneratedScript {
  const { content, style, duration, showName = "The Show" } = options;
  
  // Extract key themes and topics from content
  const words = content.toLowerCase().split(/\s+/);
  const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 10);
  const firstSentence = sentences[0]?.trim() || "Welcome to today's discussion.";
  const wordCount = words.length;
  
  // Determine category based on content keywords
  let category = "General";
  if (words.some(w => ["technology", "tech", "ai", "digital", "software"].includes(w))) category = "Technology";
  if (words.some(w => ["business", "market", "company", "finance", "economy"].includes(w))) category = "Business";
  if (words.some(w => ["health", "medical", "wellness", "fitness", "nutrition"].includes(w))) category = "Health";
  if (words.some(w => ["education", "learning", "school", "university", "study"].includes(w))) category = "Education";
  if (words.some(w => ["science", "research", "study", "discovery", "experiment"].includes(w))) category = "Science";
  
  // Extract key topics (most frequent meaningful words)
  const stopWords = new Set(["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"]);
  const meaningfulWords = words.filter(w => w.length > 4 && !stopWords.has(w));
  const wordFreq = meaningfulWords.reduce((acc, word) => {
    acc[word] = (acc[word] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const keyTopics = Object.entries(wordFreq)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .map(([word]) => word.charAt(0).toUpperCase() + word.slice(1));
  
  // Style-specific formatting
  const styleFormats = {
    conversational: {
      introTone: "friendly and welcoming",
      transitionPhrase: "So let's dive in",
      hostVoice: "casual and engaging"
    },
    professional: {
      introTone: "authoritative and polished",
      transitionPhrase: "Let's examine this in detail",
      hostVoice: "professional and informative"
    },
    educational: {
      introTone: "knowledgeable and approachable",
      transitionPhrase: "Today we'll learn about",
      hostVoice: "educational and clear"
    },
    interview: {
      introTone: "curious and engaging",
      transitionPhrase: "Our guest today brings unique insights",
      hostVoice: "inquisitive and thoughtful"
    }
  };
  
  const format = styleFormats[style as keyof typeof styleFormats] || styleFormats.conversational;
  
  // Generate realistic intro
  const intro = `[INTRO MUSIC FADES IN]

Welcome to ${showName}! I'm your host, and today we're diving into a fascinating topic that's sure to capture your attention.

[MUSIC FADES TO BACKGROUND]

${firstSentence} This is exactly the kind of story that deserves our attention, and I'm excited to break it down for you in today's episode.

[MUSIC FADES OUT]

${format.transitionPhrase}, and explore what this means for all of us. Grab your coffee, settle in, and let's get started.`;

  // Generate main content with natural breaks
  const contentChunks = sentences.slice(1, Math.min(sentences.length, 8));
  const mainContent = `Now, let me walk you through the key points of this story.

[TRANSITION MUSIC - 3 SECONDS]

First, let's establish the context. ${contentChunks[0] || "We're looking at a development that has significant implications."}

${contentChunks[1] || "The details are quite compelling when you examine them closely."} This brings us to an important consideration that affects how we should interpret these findings.

[TRANSITION MUSIC - 3 SECONDS]

What's particularly interesting is how this connects to broader trends we've been seeing. ${contentChunks[2] || "The patterns are becoming clearer as more information emerges."}

Let me break down the key implications:

${contentChunks.slice(3, 6).map((chunk, i) => `${i + 1}. ${chunk || "This aspect requires careful consideration of multiple factors."}`).join('\n\n')}

[TRANSITION MUSIC - 3 SECONDS]

Now, you might be wondering what this means for the future. ${contentChunks[6] || "The trajectory suggests several possible outcomes that are worth monitoring."} 

This is where things get really interesting, and why I wanted to share this story with you today.`;

  // Generate outro
  const outro = `[OUTRO MUSIC FADES IN]

So, what's the takeaway from all of this? I think the key insight is that ${keyTopics[0] || "this topic"} continues to evolve in ways that demand our attention.

As we wrap up today's episode, I encourage you to think about how this might impact your own perspective on ${keyTopics[1] || "related matters"}.

[MUSIC BUILDS]

Thanks for joining me on ${showName}. If you enjoyed today's discussion, don't forget to subscribe and share this episode with friends who might find it interesting.

Next time, we'll be exploring another compelling story, so make sure you're subscribed so you don't miss it.

Until then, keep questioning, keep learning, and I'll see you in the next episode.

[OUTRO MUSIC FADES OUT]`;

  // Generate timestamps based on estimated duration
  const durationMap = { "5-10": 8, "10-20": 15, "20-30": 25, "30+": 35 };
  const estimatedDuration = durationMap[duration as keyof typeof durationMap] || 15;
  
  const timestamps = [
    { time: "0:00", topic: "Introduction" },
    { time: "1:30", topic: "Topic Overview" },
    { time: `${Math.floor(estimatedDuration * 0.2)}:00`, topic: "Key Points Analysis" },
    { time: `${Math.floor(estimatedDuration * 0.5)}:00`, topic: "Main Discussion" },
    { time: `${Math.floor(estimatedDuration * 0.8)}:00`, topic: "Implications & Takeaways" },
    { time: `${estimatedDuration - 2}:00`, topic: "Wrap-up & Next Episode" }
  ];

  return {
    intro,
    mainContent,
    outro,
    showNotes: {
      keyTopics: keyTopics.length > 0 ? keyTopics : ["Analysis", "Discussion", "Insights"],
      resources: [
        "Episode transcript available on our website",
        "Follow us on social media for updates",
        "Submit topic suggestions via our contact form"
      ],
      timestamps,
      episodeDetails: {
        duration: `~${duration.replace('+', '')} minutes`,
        category,
        format: style === "interview" ? "Interview Style" : "Solo Commentary"
      }
    }
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
    console.log("Falling back to local script generation...");
    
    // Use fallback when API fails
    return generateFallbackScript(options);
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
