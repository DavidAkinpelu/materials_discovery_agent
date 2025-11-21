from exa_py import Exa
import os
from utils.cache import cache_manager
import json
from dotenv import load_dotenv
from config import settings
import asyncio
from functools import partial

load_dotenv()

exa = Exa(api_key=os.getenv("EXA_API_KEY"))

async def exa_search_tool(query: str, num_results: int = settings.DEFAULT_SEARCH_RESULTS, **kwargs) -> str:
    """
    Search the web using Exa with configurable parameters
    
    Reference: https://docs.exa.ai/reference/search
    
    Args:
        query: Natural language search query
        num_results: Number of results to return (default: 5, max: 10 for keyword, 100 for neural)
        **kwargs: Additional search parameters:
            - type: Search type - 'keyword', 'neural', 'auto' (default: 'auto')
            - category: Data category to focus on
            - user_location: Two-letter ISO country code
            - include_domains: List of domains to include
            - exclude_domains: List of domains to exclude
            - start_crawl_date: Start date for crawled content (ISO 8601)
            - end_crawl_date: End date for crawled content (ISO 8601)
            - start_published_date: Start date for published content (ISO 8601)
            - end_published_date: End date for published content (ISO 8601)
            - include_text: List with one string (max 5 words) that must be present
            - exclude_text: List with one string (max 5 words) that must not be present
            - use_autoprompt: Convert query to Exa format (default: False)
            - moderation: Enable content moderation (default: False)
    
    Returns:
        Formatted search results as JSON string
    """
    
    cache_key = f"exa_search:{query}:{num_results}:{json.dumps(kwargs, sort_keys=True)}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        search_params = {
            'query': query,
            'num_results': num_results,
            'type': kwargs.get('type', 'auto')
        }
        
        if kwargs.get('category'):
            search_params['category'] = kwargs['category']
        if kwargs.get('user_location'):
            search_params['user_location'] = kwargs['user_location']
        if kwargs.get('include_domains'):
            search_params['include_domains'] = kwargs['include_domains']
        if kwargs.get('exclude_domains'):
            search_params['exclude_domains'] = kwargs['exclude_domains']
        if kwargs.get('start_crawl_date'):
            search_params['start_crawl_date'] = kwargs['start_crawl_date']
        if kwargs.get('end_crawl_date'):
            search_params['end_crawl_date'] = kwargs['end_crawl_date']
        if kwargs.get('start_published_date'):
            search_params['start_published_date'] = kwargs['start_published_date']
        if kwargs.get('end_published_date'):
            search_params['end_published_date'] = kwargs['end_published_date']
        if kwargs.get('include_text'):
            include_text = kwargs['include_text']
            search_params['include_text'] = include_text if isinstance(include_text, list) else [include_text]
        if kwargs.get('exclude_text'):
            exclude_text = kwargs['exclude_text']
            search_params['exclude_text'] = exclude_text if isinstance(exclude_text, list) else [exclude_text]
        
        loop = asyncio.get_event_loop()
        search_response = await loop.run_in_executor(
            None, 
            partial(exa.search, **search_params)
        )
        
        formatted = []
        for result in search_response.results:
            formatted.append({
                "title": getattr(result, 'title', ''),
                "url": getattr(result, 'url', ''),
                "author": getattr(result, 'author', None),
                "published_date": getattr(result, 'published_date', None),
                "score": getattr(result, 'score', None),
                'text': getattr(result, 'text', None),
                'highlights': getattr(result, 'highlights', None),
                'summary': getattr(result, 'summary', None),
                "id": getattr(result, 'id', None)
            })
        
        result_str = json.dumps(formatted, indent=2)
        
        ttl = settings.CACHE_TTL_SEARCH_SHORT if any(word in query.lower() for word in ["price", "cost"]) else settings.CACHE_TTL_SEARCH_LONG
        cache_manager.set(cache_key, result_str, ttl=ttl)
        
        return result_str
        
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})
