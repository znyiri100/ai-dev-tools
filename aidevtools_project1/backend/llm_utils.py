import os
import google.generativeai as genai
from typing import Optional

STUDY_GUIDE_PROMPT = """You are a highly capable research assistant and tutor. Create a detailed study guide designed to review understanding of the transcript. Create a quiz with ten short-answer questions (2-3 sentences each) and include a separate answer key.

Transcript:
{transcript}"""

QUIZ_PROMPT = """Generate a quiz with 5 multiple choice questions based on the transcript.
Return the result strictly as a valid JSON array of objects.
Each object must have the following structure:
{{
    "question": "The question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "The text of the correct option (must match one of the options exactly)",
    "explanation": "Brief explanation of why this is correct"
}}
Return ONLY the JSON array. Do not include any markdown formatting (like ```json ... ```), no preamble, and no postscript.

Transcript:
{transcript}"""

def get_api_key() -> Optional[str]:
    return os.environ.get("GOOGLE_API_KEY")

def configure_genai():
    api_key = get_api_key()
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)

def generate_content(prompt_template: str, transcript: str) -> str:
    try:
        configure_genai()
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt_template.format(transcript=transcript))
        return response.text
    except ValueError as ve:
        return f"Error: {str(ve)}"
    except Exception as e:
        return f"Error generating content: {str(e)}"

def generate_study_guide(transcript: str) -> str:
    return generate_content(STUDY_GUIDE_PROMPT, transcript)

def generate_quiz(transcript: str) -> str:
    return generate_content(QUIZ_PROMPT, transcript)

CHAT_SYSTEM_PROMPT = """You are a friendly and highly capable research assistant and tutor.
Your goal is to help the user understand the SOURCE MATERIAL which is from a transcript of a video.
Be concise, encouraging, and clear in your responses.
If asked about topics outside of the SOURCE MATERIAL, politely steer the conversation back to the study material.
You are embodying the persona of a helpful tutor who loves to explain the details of the SOURCE MATERIAL.

SOURCE MATERIAL:
{study_guide}

Introduce yourself, describe the material, and ask the user a starter question about the material."""

def chat_with_study_guide(study_guide: str, message: str, history: list) -> str:
    try:
        configure_genai()
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Construct the full prompt with history
        full_prompt = CHAT_SYSTEM_PROMPT.format(study_guide=study_guide) + "\n\n"
        
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                full_prompt += f"User: {content}\n"
            elif role == "assistant":
                full_prompt += f"Assistant: {content}\n"
                
        full_prompt += f"User: {message}\nAssistant:"
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"
