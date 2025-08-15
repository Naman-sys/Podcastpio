import { type PodcastScript, type InsertPodcastScript } from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  getPodcastScript(id: string): Promise<PodcastScript | undefined>;
  createPodcastScript(script: InsertPodcastScript): Promise<PodcastScript>;
  listPodcastScripts(): Promise<PodcastScript[]>;
}

export class MemStorage implements IStorage {
  private scripts: Map<string, PodcastScript>;

  constructor() {
    this.scripts = new Map();
  }

  async getPodcastScript(id: string): Promise<PodcastScript | undefined> {
    return this.scripts.get(id);
  }

  async createPodcastScript(insertScript: InsertPodcastScript): Promise<PodcastScript> {
    const id = randomUUID();
    const script: PodcastScript = { 
      ...insertScript, 
      id,
      createdAt: new Date()
    } as PodcastScript;
    this.scripts.set(id, script);
    return script;
  }

  async listPodcastScripts(): Promise<PodcastScript[]> {
    return Array.from(this.scripts.values());
  }
}

export const storage = new MemStorage();
