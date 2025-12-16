from openai import OpenAI
from os import getenv
from dotenv import load_dotenv

print("Hi! Welcome to the penguin language app. What kind of language do you want to learn?? What kind of dificulty do you want Easy,Medium, or Hard?")
response = input()


langy = response.split()[0]
load_dotenv()
dify = response.split()[1]
client = OpenAI(
    api_key = getenv('api_key')
)

def get_standard_response(system_prompt, user_prompt):
    """
    Sends a prompt to the ChatGPT API where it will return a standard response.
    ChatGPT will not remember any prior conversations.

    Parameters:
    - system_prompt (str): Directions on how ChatGPT should act.
    - user_prompt (str): A prompt from the user.

    Returns:
    - (str): ChatGPT's response.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content
words = get_standard_response(f'you are a language tutor, return the answer as just a python list of the words as strings','give us 5 vocab words in ' + langy + ' in difficulty ' + dify)
print((get_standard_response("""you are a language tutor, return multiple choice questions you come up with in python dicionary format: {'q1':'question 1 text goes here','q1a:['potential answer 1 to question 1 goes here, potential answer 2 to question 1 goes here, ...],'q2':'question 1 text goes here','q2a':['potential answer 1 to question 2 goes here, potential answer 2 to question 2 goes here, ...]}"""
                            ,'come up with multiple choice questions with 3-4 answers only one answer being the correct translation. the questions will ask users to translate english words into ' + langy + ' words using this list of words ' +words)))