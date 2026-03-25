---
name: extract-insights
description: Extract high-signal insights from a creator's video transcripts into categorized markdown files. Use when transcripts exist under output/tiktok/{creator}/transcripts/.
---

# Extract Insights

Process a creator's video transcripts and produce categorized insight files.

## Input

The user provides a creator name. Transcripts live at:
```
output/tiktok/{creator}/transcripts/*.md
```

## Output

Insight files go to:
```
output/tiktok/{creator}/insights/{CATEGORY}.md
```

Each category file (e.g. `MINDSET.md`, `CONTENT_IDEAS.md`, `MONETIZATION.md`) groups related lessons. You decide the categories based on what the creator actually talks about. Use SCREAMING_SNAKE_CASE for filenames.

## Process

1. List all transcripts for the creator.
2. Read them in batches (10-15 at a time).
3. For each transcript, identify the core lesson and which category it belongs to.
4. If a transcript has no clear lesson (e.g. just a promo or follow CTA), skip it.
5. Write each category file, appending lessons as you go. If the file already exists, read it first and append new lessons — never overwrite existing ones.
6. After processing all transcripts, report what you created: how many lessons extracted, how many skipped, and which category files were written.

## Writing Style

Each lesson follows this format:

```markdown
## {Lesson Title}

{1-3 short paragraphs condensing the transcript into the key insight.}

{If the creator uses a specific analogy, story, or math example — preserve it with a bold label like **The wrestling story:** or **The gym math:**}

{If there's a clear actionable takeaway, add it with **How to use this:** or **The insight:**}

> Source: *"{video title from the transcript filename}"*

---
```

### Rules

- High signal-to-noise ratio. Cut filler, keep substance.
- Preserve the creator's vocabulary, analogies, and stories. Don't sanitize their voice.
- Use short, direct sentences. Lead with the point.
- Bold labels for stories/examples/takeaways (e.g. **The insight:**, **The story:**).
- No negative parallelisms ("not X — it's Y"). Just state what it is.
- No "the X is real" constructions.
- No emojis.
- Each category file starts with `# {Category Name}` as the H1.
- Lessons are separated by `---`.
- Source references use the video title extracted from the transcript filename (the part between the date and the ID).
