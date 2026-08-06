from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://lansly.ru/</loc>
    <lastmod>2026-07-17</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""


@router.get("/sitemap.xml", response_class=Response)
async def sitemap():
    return Response(content=SITEMAP_XML, media_type="application/xml")
