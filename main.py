import key
from openai import OpenAI


print("Hi! Welcome to the penguin language app. What kind of language do you want to learn?? What kind of dificulty do you want Easy,Medium, or Hard?")
response = input()


langy = response.split()[0]

dify = response.split()[1]

client = OpenAI(
    api_key = key.secret.ai
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
get_standard_response('you are a language tutor','give us 5 vocab words in ' + langy + ' in difficulty ' + dify)