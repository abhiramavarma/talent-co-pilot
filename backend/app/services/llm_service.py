import os
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from ..models import ProjectRequirement, ProjectPhase

logger = logging.getLogger(__name__)

class ProjectRequirementExtractor:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    def __init__(self):
        """Initialize Gemini API for skill extraction"""
        self.embedding_model = ProjectRequirementExtractor.embedding_model
        
        # Initialize Gemini API
        try:
            # api_key = os.getenv('GEMINI_API_KEY')
            api_key = "AIzaSyCJbcYjeXiZoUGI3bYhS8Z2s6b-CCPGfTg"
            if not api_key:
                logger.warning("GEMINI_API_KEY not found in environment variables")
                self.gemini_model = None
            else:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini API initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini API: {e}")
            self.gemini_model = None
        
    def generate_short_description(self, text: str, max_words: int = 30) -> str:
        """
        Use LLM to generate a concise project description.
        """
        prompt = (
            f"Extract a concise project description (up to {max_words} words) "
            f"from the following content:\n\n{text}"
        )
        try:
            description = self.gen_ai(prompt=prompt)
            return description.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "AI description generation failed"
        
        # Comment out local Llama 3 for now
        # try:
        #     # Use a much smaller model for faster loading
        #     model_name = "distilgpt2"  # Very small and fast model
        #     logger.info(f"Loading model: {model_name}")
        #     
        #     self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        #     self.model = AutoModelForCausalLM.from_pretrained(
        #         model_name,
        #         torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        #         device_map="auto" if torch.cuda.is_available() else None
        #     )
        #     
        #     # Add padding token if not present
        #     if self.tokenizer.pad_token is None:
        #         self.tokenizer.pad_token = self.tokenizer.eos_token
        #     
        #     self.text_generator = pipeline(
        #         "text-generation",
        #         model=self.model,
        #         tokenizer=self.tokenizer,
        #         max_length=512,
        #         temperature=0.1,
        #         do_sample=True,
        #         pad_token_id=self.tokenizer.eos_token_id
        #     )
        #     
        #     logger.info("Llama 3 model loaded successfully")
        #     
        # except Exception as e:
        #     logger.warning(f"Failed to load Llama 3, using fallback: {e}")
        #     self.text_generator = None
        
        logger.info("ProjectRequirementExtractor initialized with Gemini API")
    
    async def extract_requirements(
        self, 
        project_description: str, 
        additional_documents: List[str] = None
    ) -> ProjectRequirement:
        """Extract skill distribution from project description using Llama 3"""
        try:
            # Combine all text for analysis
            full_text = project_description
            if additional_documents:
                full_text += " " + " ".join(additional_documents)
            
            # Extract skills using Gemini API
            skill_distribution = await self._extract_skills_with_gemini(full_text)
            
            # Generate embedding for the project
            embedding = self.embedding_model.encode(full_text)
            
            # Create ProjectRequirement object with skill distribution
            project_req = ProjectRequirement(
                project_id=0,  # Will be set by the caller
                project_name=self._extract_project_name(project_description),
                description=project_description,
                project_phase=ProjectPhase.DEVELOPMENT,  # Default phase
                phase_skill_adjustments={ProjectPhase.DEVELOPMENT: skill_distribution},  # Add skill distribution
                priority_level=5,  # Default priority
                team_size_required=3,  # Default team size
                embedding_vector=embedding.tolist(),  # Add embedding vector
                created_at=datetime.utcnow()
            )
            
            logger.info(f"Extracted skills for project: {project_req.project_name}")
            return project_req
            
        except Exception as e:
            logger.error(f"Failed to extract requirements: {str(e)}")
            # Return a basic project requirement as fallback
            return self._create_fallback_requirement(project_description)
    
    async def _extract_skills_with_gemini(self, text: str) -> Dict[str, float]:
        """Extract skills using Gemini API"""
        if self.gemini_model is None:
            # Fallback to simple keyword matching
            return self._extract_skills_simple(text)
        
        try:
            # Create prompt for skill extraction
            prompt = f"""
            Analyze this project description and extract the required technical skills with their importance weights (0.0 to 1.0).
            Only return skills that are actually mentioned or clearly implied in the project description.
            Focus on common technical skills like: React, Python, JavaScript, Java, Node.js, AWS, Docker, etc.
            
            Project Description: {text}

            Return a JSON response with the following structure:
            {{
                "skill_name" : weight_percentage(0.0-1.0)
            }}
            
            Example:
            {{
                "React": 0.8,
                "JavaScript": 0.7,
                "Node.js": 0.6
            }}
            """
            
            # Generate response using Gemini API
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                skill_distribution = json.loads(json_text)
                
                # Validate and normalize the distribution
                return self._validate_and_normalize_skills(skill_distribution)
            else:
                logger.warning("No valid JSON found in Gemini response, falling back to simple matching")
                return self._extract_skills_simple(text)
                
        except Exception as e:
            logger.warning(f"Gemini API extraction failed: {e}, falling back to simple matching")
            return self._extract_skills_simple(text)
    
    def _extract_skills_simple(self, text: str) -> Dict[str, float]:
        """Simple fallback skill extraction"""
        # Common technical skills for fallback matching
        common_skills = [
            "React", "Vue.js", "Angular", "JavaScript", "TypeScript", "HTML", "CSS", "Python", "Java", 
            "Node.js", "C#", "Go", "Rust", "PHP", "Django", "Flask", "Express.js", "Spring Boot",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
            "React Native", "Flutter", "iOS", "Android", "Swift", "Kotlin", "Jest", "Cypress", "Selenium"
        ]
        
        text_lower = text.lower()
        found_skills = {}
        
        for skill in common_skills:
            skill_lower = skill.lower()
            if skill_lower in text_lower or skill in text:
                # Simple weight based on frequency
                frequency = text_lower.count(skill_lower)
                weight = min(frequency * 0.3, 1.0)
                if weight > 0.1:
                    found_skills[skill] = weight
        
        # Normalize weights to sum to 1.0
        if found_skills:
            total_weight = sum(found_skills.values())
            for skill in found_skills:
                found_skills[skill] = found_skills[skill] / total_weight
        
        return found_skills
    
    def _validate_and_normalize_skills(self, skill_distribution: Dict[str, float]) -> Dict[str, float]:
        """Validate and normalize skill distribution from LLM response"""
        validated_skills = {}
        
        for skill, weight in skill_distribution.items():
            # Ensure weight is between 0 and 1
            normalized_weight = max(0.0, min(1.0, float(weight)))
            if normalized_weight > 0.05:  # Only include skills with meaningful weight
                validated_skills[skill] = normalized_weight
        
        # Normalize weights to sum to 1.0
        if validated_skills:
            total_weight = sum(validated_skills.values())
            if total_weight > 0:
                for skill in validated_skills:
                    validated_skills[skill] = validated_skills[skill] / total_weight
        
        return validated_skills
    
    def _extract_project_name(self, description: str) -> str:
        """Extract a meaningful project name from the description"""
        # Take the first sentence or first 50 characters as project name
        first_sentence = description.split('.')[0]
        if len(first_sentence) > 60:
            first_sentence = first_sentence[:60] + "..."
        return first_sentence.strip()
    
    def _create_fallback_requirement(self, project_description: str) -> ProjectRequirement:
        """Create a basic project requirement as fallback"""
        return ProjectRequirement(
            project_id=0,
            project_name="Project",
            description=project_description,
            project_phase=ProjectPhase.DEVELOPMENT,
            priority_level=5,
            team_size_required=3,
            created_at=datetime.utcnow()
        )
    
    def generate_project_embedding(self, project_description: str) -> List[float]:
        """Generate embedding for a project description"""
        return self.embedding_model.encode(project_description).tolist()