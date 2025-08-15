# Overview

This is a podcast script generation application that converts text content or web URLs into structured podcast scripts using Google's Gemini AI. The application features a React frontend with a modern UI built using shadcn/ui components, an Express.js backend, and PostgreSQL database integration via Drizzle ORM. Users can input content either as raw text or by providing a URL, customize podcast style and duration, and receive AI-generated scripts with intro, main content, outro, and comprehensive show notes.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: React 18 with TypeScript and Vite as the build tool
- **UI Library**: shadcn/ui components built on Radix UI primitives with Tailwind CSS for styling
- **State Management**: TanStack Query (React Query) for server state management and caching
- **Routing**: Wouter for lightweight client-side routing
- **Form Handling**: React Hook Form with Zod validation via @hookform/resolvers
- **Styling**: Tailwind CSS with custom CSS variables for theming, supporting both light and dark modes

## Backend Architecture
- **Framework**: Express.js with TypeScript running on Node.js
- **API Design**: RESTful API with JSON responses
- **Request Processing**: Express middleware for JSON parsing, URL encoding, and request/response logging
- **Error Handling**: Centralized error handling middleware with proper HTTP status codes
- **Development Setup**: Hot reloading with tsx and Vite integration for development mode

## Database Architecture
- **ORM**: Drizzle ORM with PostgreSQL dialect
- **Database Provider**: Neon Database (@neondatabase/serverless) for serverless PostgreSQL
- **Schema Management**: Type-safe schema definitions with automatic TypeScript type generation
- **Migrations**: Drizzle Kit for database migrations and schema changes
- **Storage Abstraction**: Interface-based storage layer with in-memory implementation for development

## AI Integration
- **AI Provider**: Google Gemini AI via @google/genai SDK
- **Content Processing**: Web scraping capability using Cheerio for URL-based content extraction
- **Script Generation**: Structured prompt engineering to generate podcast scripts with specific formatting
- **Response Structure**: JSON-structured AI responses with intro, main content, outro, and show notes

## Data Models
- **Podcast Scripts**: Core entity storing user input, generated content, metadata, and configuration
- **Content Types**: Support for both direct text input and URL-based content fetching
- **Customization Options**: Podcast style (conversational, professional, educational, interview) and duration targeting
- **Analytics**: Word count and character count tracking for content metrics

## Development and Build System
- **Build Tool**: Vite for fast development and optimized production builds
- **TypeScript**: Full TypeScript support with strict type checking across frontend, backend, and shared code
- **Code Organization**: Monorepo structure with shared types and schemas between client and server
- **Asset Management**: Static asset serving with proper routing for both development and production
- **Path Aliases**: Organized import paths using TypeScript path mapping for cleaner code structure

# External Dependencies

## Core Framework Dependencies
- **React Ecosystem**: React 18, React DOM, React Hook Form for frontend functionality
- **Express.js**: Web framework for the Node.js backend API server
- **TypeScript**: Type safety across the entire application stack

## Database and ORM
- **Neon Database**: Serverless PostgreSQL database hosting (@neondatabase/serverless)
- **Drizzle ORM**: Type-safe database ORM with PostgreSQL dialect (drizzle-orm)
- **Drizzle Kit**: Database migration and schema management tool

## AI and Content Processing
- **Google Gemini AI**: AI text generation service (@google/genai)
- **Cheerio**: Server-side HTML parsing for web content extraction

## UI and Styling
- **Radix UI**: Accessible component primitives (@radix-ui/react-*)
- **Tailwind CSS**: Utility-first CSS framework with PostCSS integration
- **Lucide React**: Icon library for consistent iconography
- **class-variance-authority**: Component variant styling utility

## Development and Build Tools
- **Vite**: Frontend build tool and development server
- **ESBuild**: Fast JavaScript bundler for backend builds
- **tsx**: TypeScript execution for Node.js development
- **Wouter**: Lightweight React router for client-side navigation

## Additional Utilities
- **TanStack Query**: Server state management and caching library
- **Zod**: Schema validation for type-safe data parsing
- **date-fns**: Date manipulation and formatting utilities
- **clsx/cn**: Conditional className utilities for dynamic styling