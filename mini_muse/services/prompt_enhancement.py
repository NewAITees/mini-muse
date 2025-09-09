"""AI-powered prompt enhancement service using Ollama."""

import logging
import re
from typing import List, Dict, Any, Optional
import asyncio
import json

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from ..config import AppConfig

logger = logging.getLogger(__name__)


class PromptEnhancer:
    """AI-powered prompt enhancement using Ollama."""
    
    def __init__(self, config: AppConfig):
        """Initialize prompt enhancer.
        
        Args:
            config: Application configuration
        """
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "Ollama not available. Install with: pip install ollama"
            )
        
        self.config = config
        self.client = ollama.AsyncClient(host=config.models.ollama_host)
        self.model = config.models.ollama_model
        
        # Style templates for different types of content
        self.style_templates = {
            "photorealistic": {
                "prefix": "professional photograph, highly detailed, 8k resolution, realistic lighting",
                "suffix": "sharp focus, professional photography, masterpiece"
            },
            "artistic": {
                "prefix": "digital art, concept art, detailed illustration, vibrant colors",
                "suffix": "artstation trending, highly detailed, artistic masterpiece"
            },
            "cinematic": {
                "prefix": "cinematic lighting, dramatic composition, film photography",
                "suffix": "cinematic shot, movie still, professional cinematography"
            },
            "fantasy": {
                "prefix": "fantasy art, magical atmosphere, ethereal lighting",
                "suffix": "fantasy concept art, mystical, enchanted"
            },
            "anime": {
                "prefix": "anime style, detailed anime art, vibrant colors",
                "suffix": "anime masterpiece, studio quality animation"
            },
            "portrait": {
                "prefix": "professional portrait, detailed facial features, studio lighting",
                "suffix": "portrait photography, high quality, detailed"
            }
        }
        
        # Quality enhancers
        self.quality_boosters = [
            "masterpiece", "best quality", "ultra detailed",
            "sharp focus", "professionally lit", "high resolution",
            "perfect composition", "award winning"
        ]
        
        # Common negative prompts
        self.negative_prompts = {
            "general": "blurry, low quality, distorted, ugly, bad anatomy, deformed, mutation, extra limbs, bad proportions",
            "photorealistic": "cartoon, anime, painting, sketch, low quality, blurry, distorted",
            "artistic": "low quality, blurry, distorted, bad anatomy, poorly drawn",
            "portrait": "bad anatomy, deformed face, bad eyes, bad hands, low quality, blurry"
        }
        
        logger.info(f"PromptEnhancer initialized with model: {self.model}")
    
    async def enhance_prompt(self,
                           prompt: str,
                           style: str = "photorealistic",
                           complexity_level: str = "medium",
                           add_quality_boosters: bool = True,
                           custom_instructions: Optional[str] = None) -> Dict[str, Any]:
        """Enhance a prompt using AI.
        
        Args:
            prompt: Original prompt
            style: Style template to apply
            complexity_level: Complexity level (simple, medium, detailed)
            add_quality_boosters: Whether to add quality enhancing terms
            custom_instructions: Custom enhancement instructions
            
        Returns:
            Dictionary containing enhanced prompt and metadata
        """
        try:
            # Build enhancement instruction
            enhancement_instruction = self._build_enhancement_instruction(
                style, complexity_level, custom_instructions
            )
            
            # Create system message for Ollama
            system_message = (
                "You are an expert at enhancing prompts for AI image generation. "
                "Enhance the user's prompt to be more detailed, vivid, and specific "
                "while maintaining the original intent. Return only the enhanced prompt."
            )
            
            # Prepare full prompt
            full_prompt = f"{enhancement_instruction}\n\nOriginal prompt: {prompt}\n\nEnhanced prompt:"
            
            # Call Ollama for enhancement
            response = await self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": full_prompt}
                ],
                options={
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            )
            
            enhanced_text = response["message"]["content"].strip()
            
            # Apply style template if requested
            if style in self.style_templates:
                enhanced_text = self._apply_style_template(enhanced_text, style)
            
            # Add quality boosters if requested
            if add_quality_boosters:
                enhanced_text = self._add_quality_boosters(enhanced_text)
            
            # Generate appropriate negative prompt
            negative_prompt = self._generate_negative_prompt(style)
            
            return {
                "original_prompt": prompt,
                "enhanced_prompt": enhanced_text,
                "negative_prompt": negative_prompt,
                "style": style,
                "complexity_level": complexity_level,
                "word_count": len(enhanced_text.split()),
                "enhancement_applied": True
            }
            
        except Exception as e:
            logger.error(f"Prompt enhancement failed: {e}")
            # Fallback to template-based enhancement
            return self._fallback_enhancement(prompt, style, add_quality_boosters)
    
    def _build_enhancement_instruction(self,
                                     style: str,
                                     complexity_level: str,
                                     custom_instructions: Optional[str]) -> str:
        """Build enhancement instruction based on parameters."""
        instructions = []
        
        # Style-specific instructions
        style_instructions = {
            "photorealistic": "Focus on realistic details, lighting, camera settings, and photographic elements.",
            "artistic": "Emphasize artistic techniques, color palettes, composition, and visual style.",
            "cinematic": "Add cinematic elements like lighting, camera angles, and dramatic composition.",
            "fantasy": "Include magical elements, atmospheric details, and fantastical descriptions.",
            "anime": "Use anime-specific terminology and visual elements.",
            "portrait": "Focus on facial features, expressions, lighting, and portrait composition."
        }
        
        if style in style_instructions:
            instructions.append(style_instructions[style])
        
        # Complexity level instructions
        complexity_instructions = {
            "simple": "Keep the enhancement concise but descriptive.",
            "medium": "Add moderate detail and descriptive elements.",
            "detailed": "Provide rich, detailed descriptions with specific visual elements."
        }
        
        if complexity_level in complexity_instructions:
            instructions.append(complexity_instructions[complexity_level])
        
        # Custom instructions
        if custom_instructions:
            instructions.append(custom_instructions)
        
        return " ".join(instructions)
    
    def _apply_style_template(self, prompt: str, style: str) -> str:
        """Apply style template to prompt."""
        template = self.style_templates.get(style)
        if not template:
            return prompt
        
        # Avoid duplicate terms
        prompt_lower = prompt.lower()
        prefix_terms = [term for term in template["prefix"].split(", ") 
                       if term.lower() not in prompt_lower]
        suffix_terms = [term for term in template["suffix"].split(", ") 
                       if term.lower() not in prompt_lower]
        
        # Build enhanced prompt
        parts = []
        if prefix_terms:
            parts.append(", ".join(prefix_terms))
        parts.append(prompt)
        if suffix_terms:
            parts.append(", ".join(suffix_terms))
        
        return ", ".join(parts)
    
    def _add_quality_boosters(self, prompt: str) -> str:
        """Add quality enhancing terms to prompt."""
        prompt_lower = prompt.lower()
        applicable_boosters = [
            booster for booster in self.quality_boosters[:3]  # Limit to 3
            if booster.lower() not in prompt_lower
        ]
        
        if applicable_boosters:
            return f"{prompt}, {', '.join(applicable_boosters)}"
        
        return prompt
    
    def _generate_negative_prompt(self, style: str) -> str:
        """Generate appropriate negative prompt for style."""
        base_negative = self.negative_prompts.get("general", "")
        style_negative = self.negative_prompts.get(style, "")
        
        if style_negative:
            return f"{base_negative}, {style_negative}"
        
        return base_negative
    
    def _fallback_enhancement(self,
                            prompt: str,
                            style: str,
                            add_quality_boosters: bool) -> Dict[str, Any]:
        """Fallback enhancement when AI enhancement fails."""
        logger.warning("Using fallback enhancement (template-based)")
        
        enhanced_text = prompt
        
        # Apply style template
        if style in self.style_templates:
            enhanced_text = self._apply_style_template(enhanced_text, style)
        
        # Add quality boosters
        if add_quality_boosters:
            enhanced_text = self._add_quality_boosters(enhanced_text)
        
        negative_prompt = self._generate_negative_prompt(style)
        
        return {
            "original_prompt": prompt,
            "enhanced_prompt": enhanced_text,
            "negative_prompt": negative_prompt,
            "style": style,
            "complexity_level": "template",
            "word_count": len(enhanced_text.split()),
            "enhancement_applied": False,
            "fallback_used": True
        }
    
    async def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Analyze prompt characteristics.
        
        Args:
            prompt: Prompt to analyze
            
        Returns:
            Analysis results
        """
        try:
            analysis_instruction = (
                "Analyze this image generation prompt and provide insights about:\n"
                "1. Detected style/genre\n"
                "2. Subject matter\n"
                "3. Descriptive quality (poor/good/excellent)\n"
                "4. Suggested improvements\n"
                "Respond in JSON format."
            )
            
            response = await self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert prompt analyst. Respond only with valid JSON."},
                    {"role": "user", "content": f"{analysis_instruction}\n\nPrompt: {prompt}"}
                ],
                options={
                    "temperature": 0.3,
                    "max_tokens": 300
                }
            )
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response["message"]["content"])
            except json.JSONDecodeError:
                # Fallback analysis
                analysis = self._fallback_analysis(prompt)
            
            return {
                "prompt": prompt,
                "analysis": analysis,
                "word_count": len(prompt.split()),
                "character_count": len(prompt)
            }
            
        except Exception as e:
            logger.error(f"Prompt analysis failed: {e}")
            return {
                "prompt": prompt,
                "analysis": self._fallback_analysis(prompt),
                "word_count": len(prompt.split()),
                "character_count": len(prompt),
                "error": str(e)
            }
    
    def _fallback_analysis(self, prompt: str) -> Dict[str, Any]:
        """Fallback prompt analysis."""
        word_count = len(prompt.split())
        
        # Simple heuristic analysis
        style_keywords = {
            "photorealistic": ["photo", "realistic", "camera", "lens"],
            "artistic": ["art", "painting", "drawing", "illustration"],
            "anime": ["anime", "manga", "kawaii"],
            "fantasy": ["dragon", "magic", "fantasy", "medieval"]
        }
        
        detected_style = "general"
        for style, keywords in style_keywords.items():
            if any(keyword in prompt.lower() for keyword in keywords):
                detected_style = style
                break
        
        quality_score = "excellent" if word_count > 15 else "good" if word_count > 8 else "poor"
        
        return {
            "detected_style": detected_style,
            "quality_score": quality_score,
            "word_count": word_count,
            "suggestions": [
                "Add more descriptive details" if word_count < 10 else "Good level of detail",
                "Consider specifying artistic style" if detected_style == "general" else f"Style: {detected_style}"
            ]
        }
    
    async def generate_variations(self,
                                prompt: str,
                                count: int = 5,
                                variation_type: str = "style") -> List[Dict[str, Any]]:
        """Generate prompt variations.
        
        Args:
            prompt: Base prompt
            count: Number of variations to generate
            variation_type: Type of variation (style, detail, mood)
            
        Returns:
            List of prompt variations
        """
        variations = []
        
        if variation_type == "style":
            # Style-based variations
            styles = list(self.style_templates.keys())
            for i in range(min(count, len(styles))):
                style = styles[i]
                enhanced = await self.enhance_prompt(prompt, style=style)
                enhanced["variation_type"] = "style"
                enhanced["variation_id"] = i + 1
                variations.append(enhanced)
        
        elif variation_type == "detail":
            # Detail level variations
            complexity_levels = ["simple", "medium", "detailed"]
            for i, level in enumerate(complexity_levels[:count]):
                enhanced = await self.enhance_prompt(
                    prompt,
                    complexity_level=level
                )
                enhanced["variation_type"] = "detail"
                enhanced["variation_id"] = i + 1
                variations.append(enhanced)
        
        elif variation_type == "mood":
            # Mood variations using AI
            moods = ["dramatic", "serene", "vibrant", "mysterious", "romantic"]
            for i, mood in enumerate(moods[:count]):
                custom_instruction = f"Add {mood} mood and atmosphere"
                enhanced = await self.enhance_prompt(
                    prompt,
                    custom_instructions=custom_instruction
                )
                enhanced["variation_type"] = "mood"
                enhanced["variation_id"] = i + 1
                enhanced["mood"] = mood
                variations.append(enhanced)
        
        return variations
    
    def get_available_styles(self) -> List[str]:
        """Get list of available style templates.
        
        Returns:
            List of style names
        """
        return list(self.style_templates.keys())
    
    def get_style_description(self, style: str) -> Dict[str, str]:
        """Get description of a style template.
        
        Args:
            style: Style name
            
        Returns:
            Style template information
        """
        template = self.style_templates.get(style)
        if template:
            return {
                "name": style,
                "prefix": template["prefix"],
                "suffix": template["suffix"],
                "negative_prompt": self.negative_prompts.get(style, "")
            }
        
        return {"error": "Style not found"}


def create_prompt_enhancer(config: AppConfig) -> Optional[PromptEnhancer]:
    """Factory function to create prompt enhancer.
    
    Args:
        config: Application configuration
        
    Returns:
        PromptEnhancer instance if dependencies are available, None otherwise
    """
    try:
        return PromptEnhancer(config)
    except ImportError as e:
        logger.warning(f"Prompt enhancer not available: {e}")
        return None