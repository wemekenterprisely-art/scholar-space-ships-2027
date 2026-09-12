"""
Web search module for Ollama - gives LLM internet access.
Uses DuckDuckGo HTML search (no API key required).
"""
import re, json, urllib.request, urllib.parse
from html import unescape

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web using DuckDuckGo HTML.
    Returns list of {title, url, snippet} dicts.
    """
    results = []
    try:
        params = urllib.parse.urlencode({"q": query, "ia": "web"})
        url = f"https://html.duckduckgo.com/html/?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", "replace")

        # Extract results from DuckDuckGo HTML
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]*)"[^>]*>(.*?)</a>', html, re.S):
            result_url = m.group(1)
            title = unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()

            # Extract snippet
            snippet_m = re.search(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', html[html.find(m.group(0)):html.find(m.group(0))+2000], re.S)
            snippet = unescape(re.sub(r"<[^>]+>", "", snippet_m.group(1))).strip() if snippet_m else ""

            if title and result_url:
                results.append({
                    "title": title,
                    "url": result_url,
                    "snippet": snippet[:500],
                })

                if len(results) >= max_results:
                    break

    except Exception as e:
        print(f"  [web-search] DuckDuckGo error: {e}")

    return results


def web_fetch(url: str, max_chars: int = 5000) -> str:
    """
    Fetch a web page and return cleaned text content.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", "replace")

        # Remove scripts and styles
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S | re.I)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S | re.I)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)
        text = unescape(text)
        text = re.sub(r"\s+", " ", text).strip()

        return text[:max_chars]

    except Exception as e:
        return f"Error fetching URL: {e}"


def search_scholarships(query: str, max_results: int = 5) -> list[dict]:
    """
    Search for scholarships and return structured results.
    """
    results = web_search(f"{query} scholarship 2027", max_results)

    structured = []
    for r in results:
        structured.append({
            "title": r["title"],
            "url": r["url"],
            "description": r["snippet"],
            "source": "web-search",
        })

    return structured


def verify_scholarship(url: str) -> dict:
    """
    Fetch a scholarship page and extract key information.
    Returns structured data about the scholarship.
    """
    content = web_fetch(url, max_chars=8000)

    # Basic extraction
    info = {
        "url": url,
        "content_length": len(content),
        "has_deadline": bool(re.search(r"deadline|due date|apply by", content, re.I)),
        "has_ielts": bool(re.search(r"ielts|toefl|english test|proficiency", content, re.I)),
        "no_ielts": bool(re.search(r"no ielts|without ielts|ielts not required|moi", content, re.I)),
        "has_funding": bool(re.search(r"funded|scholarship|stipend|tuition", content, re.I)),
        "has_libya": bool(re.search(r"libya|libyan|african|developing", content, re.I)),
    }

    # Extract deadline if found
    deadline_m = re.search(r"deadline[:\s]*([\w\s,./-]+\d{4})", content, re.I)
    if deadline_m:
        info["deadline_text"] = deadline_m.group(1).strip()[:100]

    return info


# Tool definitions for Ollama function calling
TOOLS = {
    "web_search": {
        "description": "Search the web for current information about scholarships, universities, or funding opportunities.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 5)"
                }
            },
            "required": ["query"]
        }
    },
    "web_fetch": {
        "description": "Fetch and read the content of a specific web page URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch"
                }
            },
            "required": ["url"]
        }
    },
    "verify_scholarship": {
        "description": "Verify a scholarship listing by fetching its page and checking for key information like deadlines, IELTS requirements, funding status, and eligibility.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The scholarship URL to verify"
                }
            },
            "required": ["url"]
        }
    }
}


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool and return result as string."""
    if tool_name == "web_search":
        results = web_search(arguments.get("query", ""), arguments.get("max_results", 5))
        return json.dumps(results, indent=2)
    elif tool_name == "web_fetch":
        content = web_fetch(arguments.get("url", ""))
        return content
    elif tool_name == "verify_scholarship":
        info = verify_scholarship(arguments.get("url", ""))
        return json.dumps(info, indent=2)
    else:
        return f"Unknown tool: {tool_name}"
