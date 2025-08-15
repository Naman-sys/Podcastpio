import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { 
  Zap, 
  Plus, 
  Download, 
  Copy, 
  CheckCircle,
  AlertCircle,
  Mic,
  FileText,
  Link as LinkIcon,
  ChevronDown
} from "lucide-react";
import type { GenerateScriptRequest, PodcastScript } from "@shared/schema";

interface FetchedContent {
  title: string;
  content: string;
  wordCount: number;
}

export default function Home() {
  const [inputTab, setInputTab] = useState<"text" | "url">("text");
  const [scriptSection, setScriptSection] = useState<"intro" | "main" | "outro" | "notes">("intro");
  const [inputText, setInputText] = useState("");
  const [inputUrl, setInputUrl] = useState("");
  const [podcastStyle, setPodcastStyle] = useState<"conversational" | "professional" | "educational" | "interview">("conversational");
  const [targetDuration, setTargetDuration] = useState<"5-10" | "10-20" | "20-30" | "30+">("10-20");
  const [showName, setShowName] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [fetchedContent, setFetchedContent] = useState<FetchedContent | null>(null);
  const [generatedScript, setGeneratedScript] = useState<PodcastScript | null>(null);

  const { toast } = useToast();

  const wordCount = inputText.trim() ? inputText.trim().split(/\s+/).length : 0;
  const charCount = inputText.length;

  const fetchContentMutation = useMutation({
    mutationFn: async (url: string) => {
      const response = await apiRequest("POST", "/api/content/fetch", { url });
      return response.json() as Promise<FetchedContent>;
    },
    onSuccess: (data) => {
      setFetchedContent(data);
      toast({
        title: "Content fetched successfully",
        description: `Retrieved ${data.wordCount} words from the article.`,
      });
    },
    onError: (error) => {
      toast({
        title: "Failed to fetch content",
        description: error instanceof Error ? error.message : "Please check the URL and try again.",
        variant: "destructive",
      });
    },
  });

  const generateScriptMutation = useMutation({
    mutationFn: async (data: GenerateScriptRequest) => {
      const response = await apiRequest("POST", "/api/scripts/generate", data);
      return response.json() as Promise<PodcastScript>;
    },
    onSuccess: (script) => {
      setGeneratedScript(script);
      toast({
        title: "Script generated successfully!",
        description: "Your podcast script is ready for review.",
      });
    },
    onError: (error) => {
      toast({
        title: "Generation failed",
        description: error instanceof Error ? error.message : "Please check your input and try again.",
        variant: "destructive",
      });
    },
  });

  const exportScriptMutation = useMutation({
    mutationFn: async ({ id, format }: { id: string; format: string }) => {
      const response = await apiRequest("POST", `/api/scripts/${id}/export`, { format });
      return { blob: await response.blob(), format };
    },
    onSuccess: ({ blob, format }) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `podcast-script.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({
        title: `Exported as ${format.toUpperCase()}`,
        description: "Download should start shortly.",
      });
    },
    onError: (error) => {
      toast({
        title: "Export failed",
        description: error instanceof Error ? error.message : "Failed to export script.",
        variant: "destructive",
      });
    },
  });

  const handleFetchContent = () => {
    if (!inputUrl) {
      toast({
        title: "URL Required",
        description: "Please enter a valid URL to fetch content.",
        variant: "destructive",
      });
      return;
    }
    fetchContentMutation.mutate(inputUrl);
  };

  const handleUseContent = () => {
    if (fetchedContent) {
      setInputText(fetchedContent.content);
      setInputTab("text");
      setFetchedContent(null);
    }
  };

  const handleGenerateScript = () => {
    const content = inputText || fetchedContent?.content;
    if (!content || content.trim().length < 10) {
      toast({
        title: "Content Required",
        description: "Please provide at least 10 characters of content to generate a script.",
        variant: "destructive",
      });
      return;
    }

    const requestData: GenerateScriptRequest = {
      inputContent: content,
      inputType: inputTab,
      sourceUrl: inputTab === "url" ? inputUrl : undefined,
      podcastStyle,
      targetDuration,
      showName: showName || undefined,
      wordCount: content.trim().split(/\s+/).length,
      charCount: content.length,
    };

    generateScriptMutation.mutate(requestData);
  };

  const handleCopyScript = () => {
    if (!generatedScript?.script) return;
    
    const scriptText = `${generatedScript.title || "Podcast Script"}\n\n` +
                      `INTRO:\n${generatedScript.script.intro}\n\n` +
                      `MAIN CONTENT:\n${generatedScript.script.mainContent}\n\n` +
                      `OUTRO:\n${generatedScript.script.outro}`;
    
    navigator.clipboard.writeText(scriptText).then(() => {
      toast({
        title: "Copied to clipboard!",
        description: "Script content has been copied.",
      });
    });
  };

  const handleExport = (format: string) => {
    if (!generatedScript) return;
    exportScriptMutation.mutate({ id: generatedScript.id, format });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <CheckCircle className="h-8 w-8 text-primary" />
                <span className="ml-2 text-xl font-bold text-slate-900">PodcastAI</span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" data-testid="button-documentation">
                Documentation
              </Button>
              <Button size="sm" data-testid="button-get-started">
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="gradient-bg py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
              Transform Content into
              <span className="text-yellow-accent"> Professional Podcasts</span>
            </h1>
            <p className="text-xl text-white/90 mb-8 max-w-3xl mx-auto">
              AI-powered tool that converts transcripts and articles into polished podcast scripts with intro/outro segments, show notes, and seamless transitions.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="bg-white text-primary hover:bg-slate-50 shadow-xl" data-testid="button-start-creating">
                Start Creating
              </Button>
              <Button variant="outline" size="lg" className="border-2 border-white text-white hover:bg-white hover:text-primary" data-testid="button-watch-demo">
                Watch Demo
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Main Application */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        
        {/* Workflow Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-center mb-6">
            <div className="flex items-center w-full max-w-2xl">
              <div className="flex items-center text-primary">
                <div className="flex items-center justify-center w-8 h-8 bg-primary text-white rounded-full text-sm font-semibold">1</div>
                <span className="ml-2 font-medium">Input Content</span>
              </div>
              <div className="flex-1 h-1 mx-4 bg-slate-200 rounded">
                <div className="h-1 bg-primary rounded w-1/3"></div>
              </div>
              <div className="flex items-center text-slate-400">
                <div className="flex items-center justify-center w-8 h-8 bg-slate-200 text-slate-600 rounded-full text-sm font-semibold">2</div>
                <span className="ml-2 font-medium">AI Processing</span>
              </div>
              <div className="flex-1 h-1 mx-4 bg-slate-200 rounded">
                <div className="h-1 bg-slate-200 rounded w-0"></div>
              </div>
              <div className="flex items-center text-slate-400">
                <div className="flex items-center justify-center w-8 h-8 bg-slate-200 text-slate-600 rounded-full text-sm font-semibold">3</div>
                <span className="ml-2 font-medium">Export Script</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Input Section */}
          <div className="space-y-6">
            <Card className="shadow-lg">
              <CardHeader>
                <div className="flex items-center">
                  <Plus className="h-6 w-6 text-primary mr-3" />
                  <CardTitle className="text-2xl">Input Content</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                
                {/* Input Method Tabs */}
                <Tabs value={inputTab} onValueChange={(value) => setInputTab(value as "text" | "url")}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="text" data-testid="tab-text">Manual Text</TabsTrigger>
                    <TabsTrigger value="url" data-testid="tab-url">URL Import</TabsTrigger>
                  </TabsList>

                  {/* Text Input Panel */}
                  <TabsContent value="text" className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        Paste Your Transcript or Article
                      </label>
                      <Textarea
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        className="h-64 resize-none"
                        placeholder="Paste your speech transcript, news article, or any text content here..."
                        data-testid="input-text-content"
                      />
                      <div className="flex justify-between items-center mt-2">
                        <span className="text-sm text-slate-500" data-testid="text-word-count">
                          {wordCount} words • {charCount} characters
                        </span>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => setInputText("")}
                          data-testid="button-clear-text"
                        >
                          Clear
                        </Button>
                      </div>
                    </div>
                  </TabsContent>

                  {/* URL Input Panel */}
                  <TabsContent value="url" className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        Article or Transcript URL
                      </label>
                      <div className="flex">
                        <Input
                          type="url"
                          value={inputUrl}
                          onChange={(e) => setInputUrl(e.target.value)}
                          className="rounded-r-none"
                          placeholder="https://example.com/article"
                          data-testid="input-url"
                        />
                        <Button 
                          onClick={handleFetchContent}
                          disabled={fetchContentMutation.isPending}
                          className="rounded-l-none"
                          data-testid="button-fetch-url"
                        >
                          {fetchContentMutation.isPending ? "Fetching..." : "Fetch"}
                        </Button>
                      </div>
                      <p className="text-sm text-slate-500 mt-2">
                        Supports articles from major news sites and transcript platforms
                      </p>
                    </div>
                    
                    {/* Fetched Content Preview */}
                    {fetchedContent && (
                      <Card className="bg-slate-50">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-semibold">Fetched Content Preview</CardTitle>
                          <p className="text-sm text-slate-600" data-testid="text-fetched-title">
                            {fetchedContent.title}
                          </p>
                        </CardHeader>
                        <CardContent>
                          <div className="text-sm text-slate-700 bg-white p-3 rounded-lg max-h-32 overflow-y-auto mb-3" data-testid="text-fetched-content">
                            {fetchedContent.content.substring(0, 200)}...
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-500">
                              Retrieved {fetchedContent.wordCount} words
                            </span>
                            <Button 
                              size="sm" 
                              variant="link"
                              onClick={handleUseContent}
                              data-testid="button-use-content"
                            >
                              Use This Content
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </TabsContent>
                </Tabs>

                {/* Advanced Options */}
                <div className="border-t pt-6">
                  <Button
                    variant="ghost"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="flex items-center justify-between w-full p-0 h-auto"
                    data-testid="button-advanced-options"
                  >
                    <span className="text-sm font-medium text-slate-700">Advanced Options</span>
                    <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
                  </Button>
                  
                  {showAdvanced && (
                    <div className="mt-4 space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-1">
                            Podcast Style
                          </label>
                          <Select value={podcastStyle} onValueChange={setPodcastStyle}>
                            <SelectTrigger data-testid="select-podcast-style">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="conversational">Conversational</SelectItem>
                              <SelectItem value="professional">Professional News</SelectItem>
                              <SelectItem value="educational">Educational</SelectItem>
                              <SelectItem value="interview">Interview Style</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-1">
                            Target Duration
                          </label>
                          <Select value={targetDuration} onValueChange={setTargetDuration}>
                            <SelectTrigger data-testid="select-target-duration">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="5-10">5-10 minutes</SelectItem>
                              <SelectItem value="10-20">10-20 minutes</SelectItem>
                              <SelectItem value="20-30">20-30 minutes</SelectItem>
                              <SelectItem value="30+">30+ minutes</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                          Show Name (Optional)
                        </label>
                        <Input
                          value={showName}
                          onChange={(e) => setShowName(e.target.value)}
                          placeholder="Tech Today, News Weekly, etc."
                          data-testid="input-show-name"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Generate Button */}
                <Button 
                  onClick={handleGenerateScript}
                  disabled={generateScriptMutation.isPending || (!inputText && !fetchedContent)}
                  className="w-full h-12 text-lg font-semibold shadow-lg hover:scale-105 transition-all"
                  data-testid="button-generate-script"
                >
                  <Zap className="h-5 w-5 mr-2" />
                  {generateScriptMutation.isPending ? "Generating Script..." : "Generate Podcast Script"}
                </Button>
              </CardContent>
            </Card>

            {/* API Status Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">API Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="h-3 w-3 bg-accent rounded-full mr-3"></div>
                      <span className="text-sm text-slate-700">Gemini API</span>
                    </div>
                    <Badge variant="secondary" className="bg-accent text-white" data-testid="status-gemini-api">
                      Connected
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="h-3 w-3 bg-slate-300 rounded-full mr-3"></div>
                      <span className="text-sm text-slate-700">Usage Today</span>
                    </div>
                    <span className="text-sm text-slate-600" data-testid="text-usage-today">247/1000 requests</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Output Section */}
          <div className="space-y-6">
            
            {/* Processing State */}
            {generateScriptMutation.isPending && (
              <Card className="shadow-lg">
                <CardContent className="py-12">
                  <div className="text-center">
                    <div className="animate-spin h-12 w-12 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
                    <h3 className="text-xl font-semibold text-slate-900 mb-2">Generating Your Podcast Script</h3>
                    <p className="text-slate-600 mb-6">AI is analyzing your content and creating professional podcast segments...</p>
                    
                    <div className="max-w-md mx-auto">
                      <div className="flex justify-between text-sm text-slate-600 mb-2">
                        <span>Progress</span>
                        <span data-testid="text-processing-percent">Processing...</span>
                      </div>
                      <Progress value={75} className="h-2" />
                    </div>
                    
                    <div className="mt-6 text-left bg-slate-50 rounded-xl p-4 max-w-md mx-auto">
                      <div className="text-sm text-slate-600 space-y-2">
                        <div className="flex items-center">
                          <div className="h-2 w-2 bg-accent rounded-full mr-3"></div>
                          Content analysis complete
                        </div>
                        <div className="flex items-center">
                          <div className="h-2 w-2 bg-primary rounded-full mr-3 animate-pulse"></div>
                          Creating intro segment
                        </div>
                        <div className="flex items-center">
                          <div className="h-2 w-2 bg-slate-300 rounded-full mr-3"></div>
                          Generating show notes
                        </div>
                        <div className="flex items-center">
                          <div className="h-2 w-2 bg-slate-300 rounded-full mr-3"></div>
                          Adding transitions
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Generated Script Output */}
            {generatedScript && generatedScript.script && (
              <Card className="shadow-lg">
                <CardHeader className="border-b">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-2xl">Generated Podcast Script</CardTitle>
                    <div className="flex space-x-2">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={handleCopyScript}
                        data-testid="button-copy-script"
                      >
                        <Copy className="h-5 w-5" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleExport("txt")}
                        disabled={exportScriptMutation.isPending}
                        data-testid="button-download-script"
                      >
                        <Download className="h-5 w-5" />
                      </Button>
                    </div>
                  </div>
                  
                  {/* Script Navigation */}
                  <Tabs value={scriptSection} onValueChange={(value) => setScriptSection(value as any)}>
                    <TabsList className="grid w-full grid-cols-4">
                      <TabsTrigger value="intro" data-testid="tab-intro">Intro</TabsTrigger>
                      <TabsTrigger value="main" data-testid="tab-main">Main Content</TabsTrigger>
                      <TabsTrigger value="outro" data-testid="tab-outro">Outro</TabsTrigger>
                      <TabsTrigger value="notes" data-testid="tab-notes">Show Notes</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </CardHeader>

                {/* Script Content */}
                <CardContent className="max-h-96 overflow-y-auto">
                  <Tabs value={scriptSection}>
                    {/* Intro Section */}
                    <TabsContent value="intro">
                      <Card className="bg-blue-50 border-l-4 border-blue-400">
                        <CardContent className="p-4">
                          <div className="prose text-slate-900 max-w-none" data-testid="content-intro">
                            {generatedScript.script.intro.split('\n').map((paragraph, index) => (
                              <p key={index} className="mb-3">{paragraph}</p>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </TabsContent>

                    {/* Main Content Section */}
                    <TabsContent value="main">
                      <Card className="bg-emerald-50 border-l-4 border-emerald-400">
                        <CardContent className="p-4">
                          <div className="prose text-slate-900 max-w-none" data-testid="content-main">
                            {generatedScript.script.mainContent.split('\n').map((paragraph, index) => (
                              <p key={index} className="mb-3">{paragraph}</p>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </TabsContent>

                    {/* Outro Section */}
                    <TabsContent value="outro">
                      <Card className="bg-orange-50 border-l-4 border-orange-400">
                        <CardContent className="p-4">
                          <div className="prose text-slate-900 max-w-none" data-testid="content-outro">
                            {generatedScript.script.outro.split('\n').map((paragraph, index) => (
                              <p key={index} className="mb-3">{paragraph}</p>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </TabsContent>

                    {/* Show Notes Section */}
                    <TabsContent value="notes">
                      <Card className="bg-slate-50">
                        <CardContent className="p-6">
                          <h3 className="font-semibold text-slate-900 mb-4">Episode Show Notes</h3>
                          
                          <div className="space-y-6" data-testid="content-show-notes">
                            <div>
                              <h4 className="font-medium text-slate-800 mb-2">Key Topics Covered:</h4>
                              <ul className="text-sm text-slate-600 space-y-1 ml-4">
                                {generatedScript.script.showNotes.keyTopics.map((topic, index) => (
                                  <li key={index}>• {topic}</li>
                                ))}
                              </ul>
                            </div>
                            
                            <div>
                              <h4 className="font-medium text-slate-800 mb-2">Resources Mentioned:</h4>
                              <ul className="text-sm text-slate-600 space-y-1 ml-4">
                                {generatedScript.script.showNotes.resources.map((resource, index) => (
                                  <li key={index}>• {resource}</li>
                                ))}
                              </ul>
                            </div>
                            
                            <div>
                              <h4 className="font-medium text-slate-800 mb-2">Timestamps:</h4>
                              <ul className="text-sm text-slate-600 space-y-1 ml-4">
                                {generatedScript.script.showNotes.timestamps.map((timestamp, index) => (
                                  <li key={index}>• {timestamp.time} - {timestamp.topic}</li>
                                ))}
                              </ul>
                            </div>
                            
                            <div className="pt-4 border-t border-slate-200">
                              <h4 className="font-medium text-slate-800 mb-2">Episode Details:</h4>
                              <div className="text-sm text-slate-600 grid grid-cols-2 gap-4">
                                <div>
                                  <span className="font-medium">Duration:</span> {generatedScript.script.showNotes.episodeDetails.duration}
                                </div>
                                <div>
                                  <span className="font-medium">Category:</span> {generatedScript.script.showNotes.episodeDetails.category}
                                </div>
                                <div>
                                  <span className="font-medium">Format:</span> {generatedScript.script.showNotes.episodeDetails.format}
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </TabsContent>
                  </Tabs>
                </CardContent>

                {/* Export Options */}
                <div className="border-t p-6">
                  <h3 className="font-semibold text-slate-900 mb-4">Export Options</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleExport("txt")}
                      disabled={exportScriptMutation.isPending}
                      data-testid="button-export-txt"
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      Text File
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleExport("json")}
                      disabled={exportScriptMutation.isPending}
                      data-testid="button-export-json"
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      JSON
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            {/* Empty State */}
            {!generateScriptMutation.isPending && !generatedScript && (
              <Card className="shadow-lg">
                <CardContent className="py-12">
                  <div className="text-center">
                    <Mic className="h-16 w-16 text-slate-300 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-slate-900 mb-2">Ready to Generate</h3>
                    <p className="text-slate-600">
                      Add your content and click "Generate Podcast Script" to create your professional podcast script.
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
