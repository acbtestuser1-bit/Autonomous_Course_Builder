"""
Serper API Service
Handles all interactions with Serper API for current references and industry examples.
"""

import aiohttp
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SerperSearchService:
    """Service for searching current articles and references using Serper API."""
    
    def __init__(self, api_key: str):
        """Initialize Serper service."""
        if not api_key:
            raise ValueError("Serper API key is required for current content integration")
        
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"
        self.headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
    
    async def search_academic_articles(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search for academic articles and recent publications."""
        academic_query = f"{query} academic articles research papers 2024 2025"
        
        payload = {
            'q': academic_query,
            'num': num_results,
            'hl': 'en',
            'gl': 'us'
        }
        
        return await self._execute_search(payload)
    
    async def search_industry_resources(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search for industry reports and business resources."""
        industry_query = f"{query} business report industry analysis case study 2024 2025"
        
        payload = {
            'q': industry_query,
            'num': num_results,
            'hl': 'en',
            'gl': 'us'
        }
        
        return await self._execute_search(payload)
    
    async def _execute_search(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute search request to Serper API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_search_results(data)
                    else:
                        logger.warning(f"Serper API request failed with status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching with Serper API: {e}")
            return []
    
    def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Serper API response."""
        results = []
        
        organic = data.get('organic', [])
        for item in organic:
            result = {
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'source': item.get('source', ''),
                'date': item.get('date', ''),
                'type': 'article'
            }
            if result['title'] and result['link']:
                results.append(result)
        
        news = data.get('news', [])
        for item in news:
            result = {
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'source': item.get('source', ''),
                'date': item.get('date', ''),
                'type': 'news'
            }
            if result['title'] and result['link']:
                results.append(result)
        
        return results
    
    def format_references_for_prompt(self, search_results: List[Dict[str, Any]], max_refs: int = 5) -> str:
        """Format search results for inclusion in AI prompts."""
        if not search_results:
            return "No current references found."
        
        formatted_refs = []
        for i, ref in enumerate(search_results[:max_refs], 1):
            formatted_ref = f"""
{i}. **{ref['title']}**
   - Source: {ref['source']}
   - URL: {ref['link']}
   - Summary: {ref['snippet'][:200]}...
   - Date: {ref.get('date', 'Recent')}
"""
            formatted_refs.append(formatted_ref)
        
        return "\n".join(formatted_refs)
    
    def format_references_for_content(self, search_results: List[Dict[str, Any]], max_refs: int = 5) -> str:
        """Format search results for inclusion in generated content."""
        if not search_results:
            return "\n**Additional Resources:**\nFor the most current information, please search academic databases and recent publications.\n"
        
        formatted_content = "\n**Current References and Resources:**\n"
        
        for i, ref in enumerate(search_results[:max_refs], 1):
            formatted_content += f"\n{i}. [{ref['title']}]({ref['link']})\n"
            formatted_content += f"   *Source: {ref['source']}*\n"
            if ref.get('date'):
                formatted_content += f"   *Published: {ref['date']}*\n"
            formatted_content += f"   {ref['snippet'][:150]}...\n"
        
        formatted_content += f"\n*References searched and updated: {datetime.now().strftime('%Y-%m-%d')}*\n"
        
        return formatted_content
