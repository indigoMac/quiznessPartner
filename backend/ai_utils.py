import os
import json
import fitz  # PyMuPDF
import tempfile
import openai
from typing import List, Dict, Any

# Get OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY", "")

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(pdf_file.read())
        temp_file_path = temp_file.name
    
    try:
        doc = fitz.open(temp_file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    finally:
        os.unlink(temp_file_path)  # Delete the temporary file

def split_text(text: str, chunk_size: int = 3000, chunk_overlap: int = 200) -> List[str]:
    """Split text into manageable chunks for processing."""
    # Simple text splitter
    chunks = []
    current_chunk = ""
    sentences = text.split(". ")
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def generate_quiz_from_text(text: str, topic: str = None, num_questions: int = 5) -> List[Dict[str, Any]]:
    """Generate a quiz from text using OpenAI."""
    
    if len(text) > 4000:
        # If text is too long, take a relevant portion
        chunks = split_text(text)
        # For simplicity, just use the first chunk
        text = chunks[0]
    
    topic_str = f"on the topic of {topic}" if topic else "based on the following content"
    
    prompt = f"""
    Create a multiple-choice quiz {topic_str}. 
    Generate {num_questions} challenging but fair questions.
    
    Text: {text}
    
    Format your response as a valid JSON array with objects containing:
    1. 'question': The question text
    2. 'options': An array of 4 possible answers (as strings)
    3. 'correct_answer': The index (0-3) of the correct answer in the options array
    
    ONLY return the JSON array, nothing else.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates quiz questions in JSON format. Only return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        result = response.choices[0].message.content.strip()
        
        # Clean up the result to ensure it's valid JSON
        # Sometimes the model returns markdown-formatted JSON
        if result.startswith("```json"):
            result = result.replace("```json", "", 1)
        if result.endswith("```"):
            result = result.replace("```", "", 1)
            
        result = result.strip()
        
        try:
            questions = json.loads(result)
            
            # Validate the structure of each question
            for q in questions:
                if "question" not in q or "options" not in q or "correct_answer" not in q:
                    raise ValueError("Invalid question structure")
                if not isinstance(q["options"], list) or len(q["options"]) < 2:
                    raise ValueError("Options must be a list with at least 2 items")
                if not isinstance(q["correct_answer"], int):
                    q["correct_answer"] = int(q["correct_answer"])
                    
            return questions
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Received text: {result}")
            # Return fallback questions
            return get_fallback_questions(topic)
            
    except Exception as e:
        print(f"Error generating quiz: {e}")
        # Return a simple default quiz if there's an error
        return get_fallback_questions(topic)

def get_fallback_questions(topic: str = None) -> List[Dict[str, Any]]:
    """Generate fallback questions if the AI fails"""
    topic_text = topic if topic else "this subject"
    
    return [
        {
            "question": f"What is the main focus of {topic_text}?",
            "options": ["Understanding concepts", "Memorizing facts", "Applying knowledge", "All of the above"],
            "correct_answer": 3
        },
        {
            "question": "Which learning method is generally most effective?",
            "options": ["Reading without taking notes", "Passive listening", "Active recall and practice", "Memorization without understanding"],
            "correct_answer": 2
        }
    ] 