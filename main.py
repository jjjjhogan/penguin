from openai import OpenAI
from os import getenv
from dotenv import load_dotenv
from json import loads


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

def get_json_response(system_prompt, user_prompt):
    """
    Sends a prompt to the ChatGPT API where it will return a JSON response.
    ChatGPT will not remember any prior conversations.

    Parameters:
    - system_prompt (str): Directions on how ChatGPT should act. Remember that it must request for a JSON response and include a JSON template.
    - user_prompt (str): A prompt from the user.
    
    Returns:
    - (dict): A dictionary containing ChatGPT's response in the requested JSON format.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return loads(response.choices[0].message.content)

words = get_standard_response(f'you are a language tutor, return the answer as just a python list of the words as strings','give us 5 vocab words in ' + langy + ' in difficulty ' + dify)
questions = (get_json_response("""you are a language tutor, use different answers on each question, and all the correct answers are different numbers [it cant be the number 1 for all of them]. return 5 multiple choice questions you come up with in json format: {'q1':'question 1 text goes here','q1a:['potential answer 1 to question 1 goes here, potential answer 2 to question 1 goes here, ...],'q2':'question 1 text goes here','q2a':['potential answer 1 to question 2 goes here, potential answer 2 to question 2 goes here, ...]}"""
                            ,'come up with multiple choice questions with 4 answers only one answer being the correct translation. the questions will ask users to translate english words into ' + langy + ' words using this list of words ' +words))

answers = []
for e in range(5):
    print(questions[f'q{e+1}'])
    for i in range(4):
        print('#' + str(i+1) + ': ' + questions[f'q{e+1}a'][i])
    answers.append(input('What is the correct translation (1-4)'))

print(answers)

print(get_standard_response("You are a language tutor, can you tell me if the answers I got are right? The questions are provided in dictinory format with the first question being under key q1 and the answers being unedr q1a. At the end will be a list of all the answers I chosse.",
                      str(questions) +'questions are done, here is list of answers ' + str(answers)))
