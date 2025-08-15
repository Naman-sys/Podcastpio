import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, jsonb, integer } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const podcastScripts = pgTable("podcast_scripts", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  title: text("title"),
  inputContent: text("input_content").notNull(),
  inputType: varchar("input_type", { enum: ["text", "url"] }).notNull(),
  sourceUrl: text("source_url"),
  script: jsonb("script").$type<{
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
  }>(),
  podcastStyle: varchar("podcast_style", { 
    enum: ["conversational", "professional", "educational", "interview"] 
  }).default("conversational"),
  targetDuration: varchar("target_duration", { 
    enum: ["5-10", "10-20", "20-30", "30+"] 
  }).default("10-20"),
  showName: text("show_name"),
  wordCount: integer("word_count"),
  charCount: integer("char_count"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertPodcastScriptSchema = createInsertSchema(podcastScripts).omit({
  id: true,
  createdAt: true,
});

export const generateScriptSchema = z.object({
  inputContent: z.string().min(10, "Content must be at least 10 characters long"),
  inputType: z.enum(["text", "url"]),
  sourceUrl: z.string().url().optional(),
  podcastStyle: z.enum(["conversational", "professional", "educational", "interview"]).default("conversational"),
  targetDuration: z.enum(["5-10", "10-20", "20-30", "30+"]).default("10-20"),
  showName: z.string().optional(),
  wordCount: z.number().optional(),
  charCount: z.number().optional(),
});

export type InsertPodcastScript = z.infer<typeof insertPodcastScriptSchema>;
export type PodcastScript = typeof podcastScripts.$inferSelect;
export type GenerateScriptRequest = z.infer<typeof generateScriptSchema>;
