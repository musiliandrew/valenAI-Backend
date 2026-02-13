import os
import google.generativeai as genai
from django.conf import settings

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_romantic_message(
    sender_name: str,
    receiver_name: str,
    tone: str = "romantic",
    length: str = "medium",
    context: str = ""
) -> list[str]:
    """
    Generate romantic Valentine's Day messages using Gemini AI.
    
    Args:
        sender_name: Name of the person sending the message
        receiver_name: Name of the person receiving the message
        tone: Message tone - "playful", "deep", "romantic", "funny"
        length: Message length - "short" (50-100 words), "medium" (100-150 words), "long" (150-200 words)
        context: Optional relationship context or special memories
    
    Returns:
        List of 3 generated message variations
    """
    
    # Map length to word count
    length_map = {
        "short": "50-100 words",
        "medium": "100-150 words",
        "long": "150-200 words"
    }
    
    word_count = length_map.get(length, "100-150 words")
    
    # Build the prompt
    prompt = f"""You are a romantic message writer helping someone express their feelings for Valentine's Day.

Generate 3 unique, heartfelt Valentine's Day messages with these details:
- From: {sender_name}
- To: {receiver_name}
- Tone: {tone}
- Length: {word_count}
{f"- Context: {context}" if context else ""}

Requirements:
1. Each message should be authentic, personal, and emotionally engaging
2. Use the names naturally in the message
3. Avoid clichés - be creative and genuine
4. Make it feel like it's coming from {sender_name}'s heart
5. The tone should be {tone} but still romantic
6. Each message should be distinctly different from the others

Format your response as exactly 3 messages separated by "---" (three dashes on a new line).
Do not include any numbering, labels, or extra text - just the messages.
"""
    
    try:
        # Use Gemini 1.5 Flash for fast generation
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate content
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.9,  # Higher creativity
                top_p=0.95,
                top_k=40,
                max_output_tokens=1000,
            )
        )
        
        # Parse the response
        full_text = response.text.strip()
        messages = [msg.strip() for msg in full_text.split('---') if msg.strip()]
        
        # Ensure we have exactly 3 messages
        if len(messages) < 3:
            # If we got fewer, pad with variations
            while len(messages) < 3:
                messages.append(messages[0] if messages else "I love you more than words can say. ❤️")
        
        return messages[:3]  # Return exactly 3
        
    except Exception as e:
        print(f"Error generating messages: {e}")
        # Return fallback messages
        return [
            f"Dear {receiver_name}, every moment with you feels like a dream come true. You make my heart skip a beat and my world brighter. Will you be my Valentine? ❤️ - {sender_name}",
            f"{receiver_name}, from the moment I met you, I knew you were special. Your smile lights up my day and your presence makes everything better. Be mine this Valentine's Day? 💕 - {sender_name}",
            f"To my dearest {receiver_name}, you are the reason I believe in love. Every day with you is a gift, and I can't imagine my life without you. Will you be my Valentine? 💖 - {sender_name}"
        ]


def generate_gift_ideas(
    budget: str,
    interests: list[str],
    relationship_stage: str = "dating"
) -> dict:
    """
    Generate personalized gift and date ideas using Gemini AI.
    
    Args:
        budget: Budget range - "low" (<$50), "medium" ($50-$150), "high" (>$150)
        interests: List of partner's interests
        relationship_stage: "new", "dating", "serious", "married"
    
    Returns:
        Dictionary with gift ideas and date suggestions
    """
    
    budget_map = {
        "low": "under $50",
        "medium": "$50-$150",
        "high": "over $150"
    }
    
    budget_range = budget_map.get(budget, "$50-$150")
    interests_str = ", ".join(interests) if interests else "general interests"
    
    prompt = f"""You are a romantic gift advisor helping someone plan the perfect Valentine's Day.

Generate personalized gift and date ideas with these details:
- Budget: {budget_range}
- Partner's interests: {interests_str}
- Relationship stage: {relationship_stage}

Provide:
1. 3 thoughtful gift ideas (with brief descriptions)
2. 3 romantic date ideas (with brief descriptions)
3. 1 creative "wow factor" surprise idea

Make suggestions practical, romantic, and tailored to the interests and budget.
Format as JSON with keys: "gifts", "dates", "surprise"
"""
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # For now, return a simple structure
        # TODO: Parse JSON response properly
        return {
            "gifts": ["Gift idea 1", "Gift idea 2", "Gift idea 3"],
            "dates": ["Date idea 1", "Date idea 2", "Date idea 3"],
            "surprise": "Surprise idea"
        }
        
    except Exception as e:
        print(f"Error generating gift ideas: {e}")
        return {
            "gifts": ["Handwritten love letter", "Favorite flowers", "Personalized photo album"],
            "dates": ["Sunset picnic", "Cooking together", "Stargazing"],
            "surprise": "Create a scavenger hunt leading to a special gift"
        }
def generate_poem(
    sender_name: str,
    receiver_name: str,
    vibe: str = "romantic",
    context: str = ""
) -> list[dict]:
    """
    Generate romantic poems using Gemini AI.
    
    Returns a list of 3 poem objects with 'title' and 'lines' (list of strings).
    """
    
    prompt = f"""You are a romantic poet helping someone write a poem for Valentine's Day.
    
    Generate 3 unique, beautiful poems with these details:
    - From: {sender_name}
    - To: {receiver_name}
    - Vibe/Style: {vibe}
    {f"- Context: {context}" if context else ""}
    
    Requirements:
    1. Each poem should have a title.
    2. Each poem should be heartfelt and well-structured.
    3. The vibe should be {vibe}.
    4. Each poem should be distinctly different.
    
    Format your response as a valid JSON list of objects:
    [
      {{
        "title": "Poem Title",
        "author": "{sender_name}",
        "lines": ["Line 1", "Line 2", ...]
      }},
      ...
    ]
    Do not include any extra text, only the JSON.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.9,
                max_output_tokens=1500,
                response_mime_type="application/json"
            )
        )
        
        import json
        poems = json.loads(response.text.strip())
        
        if not isinstance(poems, list):
            poems = [poems]
            
        return poems[:3]
        
    except Exception as e:
        print(f"Error generating poems: {e}")
        return [
            {
                "title": "A Moment with You",
                "author": sender_name,
                "lines": [
                    f"Dear {receiver_name}, in your eyes I see tomorrow,",
                    "A world away from any sorrow.",
                    "With every breath, with every line,",
                    "I'm glad to call you Valentine."
                ]
            }
        ]
