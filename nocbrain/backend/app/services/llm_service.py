import aiohttp
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.config import settings
from app.models import LLMResponse

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.llm_model
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    async def analyze_alerts(self, alerts: List[Dict[str, Any]]) -> LLMResponse:
        """Analyze alerts using LLM to suggest root cause"""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        if not alerts:
            raise ValueError("No alerts provided for analysis")
        
        # Prepare alert data for LLM
        alert_list = "\n".join([
            f"- {alert['severity'].upper()}: {alert['message']} (at {alert['timestamp']})"
            for alert in alerts
        ])
        
        # Create prompt
        prompt = f"""You are a senior NOC engineer.
Given these alerts:
{alert_list}

Suggest the most probable root cause in 5 concise sentences.
Focus on the most likely technical issue causing these alerts.
Be specific and actionable.

Respond with JSON format:
{{
    "root_cause": "Your root cause analysis here",
    "confidence": 0.8,
    "reasoning": "Brief explanation of your reasoning"
}}"""
        
        # Prepare request
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior NOC engineer analyzing system alerts. Always respond with valid JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if "choices" in data and len(data["choices"]) > 0:
                            content = data["choices"][0]["message"]["content"]
                            
                            try:
                                # Parse JSON response
                                llm_result = json.loads(content)
                                
                                return LLMResponse(
                                    root_cause=llm_result.get("root_cause", "Unable to determine root cause"),
                                    confidence=float(llm_result.get("confidence", 0.5)),
                                    reasoning=llm_result.get("reasoning", "No reasoning provided")
                                )
                                
                            except json.JSONDecodeError:
                                # Fallback if JSON parsing fails
                                return LLMResponse(
                                    root_cause=content,
                                    confidence=0.5,
                                    reasoning="LLM response could not be parsed as JSON"
                                )
                        else:
                            raise ValueError("No choices in LLM response")
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM API error {response.status}: {error_text}")
                        raise ValueError(f"LLM API error: {response.status}")
                        
        except aiohttp.ClientTimeout:
            logger.error("LLM request timed out")
            raise ValueError("LLM request timed out")
            
        except aiohttp.ClientError as e:
            logger.error(f"LLM client error: {e}")
            raise ValueError(f"LLM client error: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error in LLM service: {e}")
            raise ValueError(f"LLM service error: {e}")
    
    async def test_connection(self) -> bool:
        """Test LLM service connection"""
        try:
            test_alerts = [
                {
                    "severity": "high",
                    "message": "CPU usage is 95% on server web-01",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            response = await self.analyze_alerts(test_alerts)
            return bool(response.root_cause)
            
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False
