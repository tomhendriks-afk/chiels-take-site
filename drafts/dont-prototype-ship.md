---
title: The AI users who are actually winning don't prototype. They ship.
tag: Opinion
date: 2026-04-26
read_time: 4
excerpt: Cat Wu, Anthropic's Head of PM, shared three insights on Lenny's Podcast that cut straight to why most people aren't getting real value from AI yet; and what the ones who are doing differently.
---

Cat Wu, Anthropic's Head of PM, was on [Lenny's Podcast](https://www.lennysnewsletter.com/p/how-anthropics-product-team-moves) recently. Three things she said stuck with me.

The first: stop asking what AI can do. Start asking what you actually need done. Look at the tasks you do on repeat, the ones you've been putting off for months, the work that keeps falling through the cracks. That's your list. Solve those first, for yourself, before you solve them for anyone else.

For me, this was creating a personal finance overview. Ever since Mint.com disappeared I had been meaning to build some sort of master Excel sheet and keep it up to date. You guessed it, never happened. Until a few weeks ago, when I used Claude to build a personal app to keep track of my finances across a bunch of accounts. The whole thing came together over a few evenings, maybe 8 to 10 hours total, spread across a week. Not in some drag-and-drop no-code builder, but as a real application with a backend API, authentication, a data feed, and deployment to a production URL I can open on my phone. I built it using Claude, Google Apps Scripts, and Gemini as my AI programmer. I now have an accurate read on where I am across all my accounts. Vibe coded by yours truly.

Her second point is where most people give up. Getting an automation to 95% feels like progress. It isn't. If it fails one time in twenty, you're still babysitting it. You haven't automated anything, you've just created a new thing to monitor. The last few percentage points take longer than everything before them. That's not a flaw in the process. That is the process. The fix: teach Claude your preferences, close the edge cases, get it to the point where you genuinely forget it's running. The 95% solution has almost no value. The 100% solution changes your day.

The Daily Briefings and Podcasts on [Ambient-Advantage.AI](https://ambient-advantage.ai) are my personal example of this; 100% fully automated, pulled together through a pipeline I built with Claude's support over the course of a few weeks. An extra hour here and there, outside of work and family time. But I pushed, and I didn't stop until both were completely automated.

The third insight hit closest to home. Most people build something, show it off, and move on. Cat's question cuts through that: are you actually using this every single day? Because that daily use is where the value compounds. A prototype you demoed once isn't an AI win. It's a proof of concept gathering dust. Build the thing you rely on. Then build the next one.

My pipeline started with some tinkering, but through daily use it grew into something I couldn't have planned upfront; a fully automated system running in Google Cloud, pushing code to GitHub, updating the site automatically through Cloudflare. Along the way it created a need to understand how to have agents comb through information, transform it into an HTML email, generate a podcast transcript, figure out text-to-speech (hello [ElevenLabs](https://elevenlabs.io)), and on from there.

This project taught me more about Google Cloud than my previous ten years talking about it. That's what daily use actually does.

So start with something that matters to you. Solve one of your problems, and solve it well. Not solve it mostly. All the way. That's how AI starts working for you, and how your own skills grow in the process.
