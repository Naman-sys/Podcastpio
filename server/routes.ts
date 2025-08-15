import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { generateScriptSchema } from "@shared/schema";
import { generatePodcastScript, fetchContentFromUrl } from "./services/gemini";

export async function registerRoutes(app: Express): Promise<Server> {
  
  // Generate podcast script endpoint
  app.post("/api/scripts/generate", async (req, res) => {
    try {
      const validatedData = generateScriptSchema.parse(req.body);
      
      let content = validatedData.inputContent;
      
      // If URL is provided, fetch content from URL
      if (validatedData.inputType === "url" && validatedData.sourceUrl) {
        try {
          const fetchedContent = await fetchContentFromUrl(validatedData.sourceUrl);
          content = fetchedContent.content;
          validatedData.inputContent = content;
        } catch (error) {
          return res.status(400).json({ 
            message: "Failed to fetch content from URL",
            error: error instanceof Error ? error.message : "Unknown error"
          });
        }
      }

      // Generate script using Gemini
      const script = await generatePodcastScript({
        content,
        style: validatedData.podcastStyle,
        duration: validatedData.targetDuration,
        showName: validatedData.showName,
      });

      // Save to storage
      const savedScript = await storage.createPodcastScript({
        ...validatedData,
        script,
      });

      res.json(savedScript);
    } catch (error) {
      console.error("Error generating script:", error);
      res.status(500).json({ 
        message: "Failed to generate podcast script",
        error: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  // Fetch content from URL endpoint
  app.post("/api/content/fetch", async (req, res) => {
    try {
      const { url } = req.body;
      
      if (!url || typeof url !== 'string') {
        return res.status(400).json({ message: "URL is required" });
      }

      const fetchedContent = await fetchContentFromUrl(url);
      res.json(fetchedContent);
    } catch (error) {
      console.error("Error fetching content:", error);
      res.status(500).json({ 
        message: "Failed to fetch content from URL",
        error: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  // Get script by ID
  app.get("/api/scripts/:id", async (req, res) => {
    try {
      const script = await storage.getPodcastScript(req.params.id);
      if (!script) {
        return res.status(404).json({ message: "Script not found" });
      }
      res.json(script);
    } catch (error) {
      console.error("Error fetching script:", error);
      res.status(500).json({ 
        message: "Failed to fetch script",
        error: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  // Export script in different formats
  app.post("/api/scripts/:id/export", async (req, res) => {
    try {
      const { format } = req.body;
      const script = await storage.getPodcastScript(req.params.id);
      
      if (!script) {
        return res.status(404).json({ message: "Script not found" });
      }

      if (!script.script) {
        return res.status(400).json({ message: "Script content not available" });
      }

      let content = "";
      let filename = `podcast-script-${script.id}`;
      let contentType = "text/plain";

      switch (format) {
        case "txt":
          content = `${script.title || "Podcast Script"}\n\n` +
                   `INTRO:\n${script.script.intro}\n\n` +
                   `MAIN CONTENT:\n${script.script.mainContent}\n\n` +
                   `OUTRO:\n${script.script.outro}\n\n` +
                   `SHOW NOTES:\n${JSON.stringify(script.script.showNotes, null, 2)}`;
          filename += ".txt";
          break;
        
        case "json":
          content = JSON.stringify(script, null, 2);
          filename += ".json";
          contentType = "application/json";
          break;
        
        default:
          return res.status(400).json({ message: "Unsupported export format" });
      }

      res.setHeader("Content-Type", contentType);
      res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);
      res.send(content);
    } catch (error) {
      console.error("Error exporting script:", error);
      res.status(500).json({ 
        message: "Failed to export script",
        error: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
