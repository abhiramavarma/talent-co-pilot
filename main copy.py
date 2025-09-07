from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

from fastapi import UploadFile, File, HTTPException
import base64
from google.generativeai import GenerativeModel, configure
from google.generativeai.types import GenerationConfig
import os
import json
from fastapi.responses import JSONResponse

@app.post("/api/analyze-document")
async def analyze_document(file: UploadFile = File(...)):
    """Process documents with Google GenAI"""
    try:
        contents = await file.read()
        configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = GenerativeModel('gemini-2.5-Flash')
        
        # Handle different file types
        if file.content_type.startswith('image/'):
            file_part = {
                "mime_type": file.content_type,
                "data": base64.b64encode(contents).decode('utf-8')
            }
        else:
            file_part = {
                "mime_type": file.content_type,
                "data": contents.decode('utf-8')
            }
        text_part = {
            "text": "Analyze the attached project document. Extract project name, description, and skills."
        }

        response = await model.generate_content(
            contents=[text_part["text"], file_part],
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "projectName": {"type": "string"},
                        "projectDescription": {"type": "string"},
                        "projectSkills": {"type": "array", "items": {"type": "string"}},
                    }
                }
            )
        )
        return JSONResponse(content=json.loads(response.text))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Document analysis failed")

@app.post("/api/analyze-team")
async def analyze_team(request_data: dict):
    """Get team recommendations from Google GenAI"""
    try:
        ai = GoogleGenAI(api_key=os.getenv("GEMINI_API_KEY"))
        response = await ai.models.generate_content(
            model="gemini-2.5-flash",
            contents=request_data["prompt"],
            config={
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": Type.OBJECT,
                    "properties": {
                        "bestMatches": {"type": Type.ARRAY},
                        "trainingRecommendations": {"type": Type.ARRAY}
                    }
                }
            }
        )
        return JSONResponse(content=json.loads(response.text))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Team analysis failed")