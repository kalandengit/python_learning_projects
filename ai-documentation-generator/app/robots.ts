import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const siteUrl = process.env.NEXT_PUBLIC_APP_URL ?? "https://docupilot.ai";
  return {
    rules: [
      { userAgent: "*", allow: "/", disallow: ["/dashboard", "/admin", "/settings", "/team", "/api"] }
    ],
    sitemap: `${siteUrl}/sitemap.xml`
  };
}
