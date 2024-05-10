import csv
import string
from pprint import pprint
import anthropic

from words import find_invalid_words, allowed_words_list

anthropic_client = anthropic.Anthropic()

def generate_prompt(allowed_words, topic, prior_texts='', prior_invalid_words=''):
    allowed_word_list_string = ','.join(allowed_words)
    repair=""
    if prior_invalid_words:
        repair = f"A previous tries failed so far:\n{prior_texts}\nThese words were NOT allowed and caused past tries to fail: {prior_invalid_words}. Fix the sentences so it uses good grammar and only uses words that are allowed. Use alternate words for the rejected words, as needed. If you introduce new terms, be sure that they are allowed or you will cause a failure!"
    return f"""Provide explanations using the allowed word list:`{allowed_word_list_string}`.
        Explain the topic using `explanation_schema` using 2 sentences of explanation text.
        Ensure all words in the explanation come from the provided word list, except for the topic itself.
        Provide a clear plan before delivering the final output, output JSON format only with the planning property and output property strings.
        For good grammar you should appropiately use these symbols: `.`, `;`, `:`, `,`, `?`, and `'`.
        You can use contractions. This is valid: `Good sun today; isn't it nice? Let's walk, and play: a great day!`
        Example explanation of `space shuttle`:
        `A space shuttle is a machine that can fly above the air, to travel in space like a space car. It can carry people and things into space.`
        
        Now, this is the topic you need to explain: `{topic}`.
        
        {repair}
        BE SURE TO ONLY USE THE ALLOWED WORDS AND THEIR PLURAL VARIATIONS, WITH GOOD GRAMMAR!"""

# Set up the JSON schema for the explanation response
explanation_schema = {
    "type": "object",
    "properties": {
        "planning": {
            "type": "string",
            "description": "Detailed planning of the explanation in a step-by-step manner."
        },
        "output": {
            "type": "string",
            "description": "Final explanation, adhering to the vocabulary list."
        }
    },
    "required": ["planning", "output"]
}




def make_explanation(topic, allowed_words_list=allowed_words_list, max_attempts=5):
    # Set up retry loop with prior attempts and invalid words
    message_history = []
    attempts = 0
    all_prior_texts = ''
    all_invalid_words = []

    while attempts < max_attempts:
        # Generate the prompt message
        prompt = generate_prompt(allowed_words_list, topic, all_prior_texts, ', '.join(all_invalid_words))

        # Set up the Anthropic API call with the explanation schema
        FAST = "claude-3-haiku-20240307"
        BEST = "claude-3-sonnet-20240229"
        message = anthropic_client.beta.tools.messages.create(
            model=BEST,
            max_tokens=1024,
            tools=[
                {
                    "name": "explanation_schema",
                    "description": "Show working out with a step-by-step plan for how to use the restricted word list to explain the topic.",
                    "input_schema": explanation_schema,
                }
            ],
            system=f"Output explanations that only use words from the allowed word list plus the term itself. Use good grammar. These words are allowed:`{','.join(allowed_words_list)}`, also plural variations that have (s or es endings, e.g: `go` is in the list, but `goes` is allowed too, `car` is in the list, but `cars` is allowed too. `animal` is in the list, so `animals` is allowed too - you get the pattern). You must use the explanation_schema output format only, no markdown. Use good grammar! The text should sound normal as much as possible.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ],
                }
            ]
        )

        # Get the response as a dictionary
        response = message.to_dict()
        pprint(response)
        if len(response['content']) == 1:
            output_data = response['content'][0]['input']
            planning = output_data.get('planning', 'No separate planning provided')
            output = output_data.get('output', 'No output provided')
        else:
            output_data = response['content'][1]['input']
            planning = output_data.get('planning', str(response['content'][0]))
            output = output_data.get('output', 'No output provided')

        # Validate the output
        extra_terms = topic.split(' ')
        invalid_words = find_invalid_words(output, allowed_words_list, extra_terms)
        
        
        # Log the message history
        message_history.append({
            "attempt": attempts + 1,
            "planning": planning,
            "output": output,
            "invalid_words": invalid_words
        })

        if not invalid_words:
            return output  # Return explanation if valid
        print("Invalid words: ", invalid_words)

        attempts += 1

        all_prior_texts = '\n'.join([entry['output'] for entry in message_history])
        all_invalid_words = sorted(set([word for entry in message_history for word in entry['invalid_words']] + invalid_words))

    # If no valid explanation found, raise an exception
    raise Exception(f"Unable to generate a valid explanation for {topic} after {max_attempts} attempts.")


make_explanation("global warming", allowed_words_list,5)
