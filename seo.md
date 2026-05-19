# SEO Fixes for bensbasil.in

## 1. Add `robots.txt`

Create a file at the site root: `robots.txt`

```
User-agent: *
Allow: /
Sitemap: https://bensbasil.in/sitemap.xml
```

---

## 2. Add `sitemap.xml`

Create a file at the site root: `sitemap.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://bensbasil.in/</loc>
    <priority>1.0</priority>
    <changefreq>monthly</changefreq>
  </url>
  <url>
    <loc>https://bensbasil.in/contact.html</loc>
    <priority>0.8</priority>
    <changefreq>monthly</changefreq>
  </url>
  <url>
    <loc>https://bensbasil.in/quiz/</loc>
    <priority>0.7</priority>
    <changefreq>monthly</changefreq>
  </url>
  <url>
    <loc>https://bensbasil.in/medical-rag-app-deploy/</loc>
    <priority>0.7</priority>
    <changefreq>monthly</changefreq>
  </url>
</urlset>
```

---

## 3. Update `<head>` in `index.html`

Replace or update the existing `<head>` block with the following. Do not remove any existing tags — only add the ones marked **ADD**.

### Title tag (UPDATE)

```html
<title>Bens Basil — AI Full-Stack Developer & MLOps Engineer | Trivandrum</title>
```

### Meta description (ADD)

```html
<meta name="description" content="Full-stack developer and MLOps engineer based in Trivandrum, building AI-integrated web apps with FastAPI, React, PostgreSQL, and LLMs. Available for collaboration." />
```

### Canonical URL (ADD)

```html
<link rel="canonical" href="https://bensbasil.in/" />
```

### Open Graph tags — for LinkedIn/WhatsApp link previews (ADD)

```html
<meta property="og:type" content="website" />
<meta property="og:url" content="https://bensbasil.in/" />
<meta property="og:title" content="Bens Basil — AI Full-Stack Developer & MLOps Engineer" />
<meta property="og:description" content="Full-stack developer and MLOps engineer based in Trivandrum, building AI-integrated web apps with FastAPI, React, PostgreSQL, and LLMs." />
<meta property="og:image" content="https://bensbasil.in/og-image.png" />
```

> **Note:** Create an `og-image.png` (1200×630px) — a simple card with your name, title, and site URL. This is the image that appears when someone shares your link.

### Twitter/X card tags (ADD)

```html
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Bens Basil — AI Full-Stack Developer & MLOps Engineer" />
<meta name="twitter:description" content="Full-stack developer and MLOps engineer based in Trivandrum, building AI-integrated web apps with FastAPI, React, and LLMs." />
<meta name="twitter:image" content="https://bensbasil.in/og-image.png" />
```

### Structured data — JSON-LD for Google (ADD, inside `<head>`)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Bens Basil",
  "url": "https://bensbasil.in",
  "jobTitle": "AI Full-Stack Developer & MLOps Engineer",
  "sameAs": [
    "https://linkedin.com/in/bensbasil",
    "https://github.com/bensbasil"
  ],
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Trivandrum",
    "addressCountry": "IN"
  }
}
</script>
```

---

## 4. Apply the same `<head>` updates to `contact.html`

Use a page-specific title and description:

```html
<title>Contact Bens Basil — AI Full-Stack Developer | Trivandrum</title>
<meta name="description" content="Get in touch with Bens Basil for collaboration on AI, MLOps, or full-stack web development projects." />
<link rel="canonical" href="https://bensbasil.in/contact.html" />
```

---

## 5. After deployment — submit to Google Search Console

1. Go to https://search.google.com/search-console
2. Add property → enter `https://bensbasil.in`
3. Verify ownership (HTML file method is easiest)
4. Go to **Sitemaps** → submit `https://bensbasil.in/sitemap.xml`
5. Go to **URL Inspection** → enter `https://bensbasil.in/` → click **Request Indexing**

---

## Summary of files to create/edit

| File | Action |
|---|---|
| `robots.txt` | Create new at site root |
| `sitemap.xml` | Create new at site root |
| `index.html` | Update `<title>`, add meta/OG/JSON-LD tags |
| `contact.html` | Update `<title>`, add meta/canonical tags |
| `og-image.png` | Create a 1200×630px preview image |
