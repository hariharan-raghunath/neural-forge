import os
import time
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()

class MealData(BaseModel):
    meal_type: str = Field(description="breakfast, lunch, dinner, snack, or full_day")
    foods: list[str]
    calories: int
    protein: int
    carbs: int
    fats: int
    notes: str = Field(description="Very brief context, max 10 words")


client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
# client = genai.Client(vertexai=True,
#     project='neural-forge-487103',
#     location='asia-south1')

SYSTEM_INSTRUCTION = """
You are a high-speed nutrition extractor. 
Extract meal data into JSON based on typical serving sizes.
Be clinical and concise. If the user logs a full day, use 'full_day' and sum the macros.
"""


def extract_meal_info(user_input: str):
    start_time = time.time()

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type='application/json',
                response_schema=MealData,
                temperature=0.1,
            ),
        )

        meal_obj = response.parsed

        data = meal_obj.model_dump()
        data['timestamp'] = datetime.now().isoformat()
        data['raw_input'] = user_input
        data['latency'] = f"{time.time() - start_time:.2f}s"

        return data
    except Exception as e:
        print(f"Error: {e}")
        return None


def give_feedback(data: dict) -> str:
    p, c, f = data['protein'], data['carbs'], data['fats']
    calories = (p * 4) + (c * 4) + (f * 9)

    feedback_lines = [
        f"\n {data['meal_type'].upper()} LOGGED ({data['latency']})",
        f"  Foods: {', '.join(data['foods'])}",
        f" Macros: P: {p}g | C: {c}g | F: {f}g | ~{calories} kcal",
        f" Notes: {data['notes']}\n",
        " Feedback:"
    ]

    if p < 30: feedback_lines.append("   - Protein is low! Add eggs or lean meat next time.")
    if calories > 750: feedback_lines.append("   - This is a heavy meal. Adjust your next portion.")
    if not feedback_lines[5:]: feedback_lines.append("   - Perfectly balanced! Keep it up.")

    return "\n".join(feedback_lines)


def main():
    print("Neural-Forge Meal Logger")
    print("Example: 'I had 2 eggs and toast for breakfast'\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        print(" Analyzing...", end="\r")

        meal_data = extract_meal_info(user_input)
        if meal_data:
            print(give_feedback(meal_data))
            print(" Sync complete.\n")
        else:
            print(" Processing failed. Check your API key or connection.")


if __name__ == "__main__":
    main()