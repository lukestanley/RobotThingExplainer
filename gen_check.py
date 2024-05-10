import csv
import string
from pprint import pprint
import anthropic

from words import find_invalid_words, allowed_words_list

anthropic_client = anthropic.Anthropic()
FAST = "claude-3-haiku-20240307"
BEST = "claude-3-sonnet-20240229"

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


explanation_tool = {
    "name": "explanation_schema",
    "description": "Show working out with a step-by-step plan for how to use the restricted word list to explain the topic.",
    "input_schema": explanation_schema,
}

# System prompt template
system_prompt_template = (
    "Output explanations that only use words from the allowed word list plus the term itself. "
    "Use good grammar. These words are allowed: `{allowed_words}`, also plural variations that have (s or es endings, "
    "e.g: `go` is in the list, but `goes` is allowed too, `car` is in the list, but `cars` is allowed too. "
    "`animal` is in the list, so `animals` is allowed too - you get the pattern). You must use the explanation_schema "
    "output format only, no markdown. Use good grammar! The text should sound normal as much as possible."
)


def make_explanation(topic, allowed_words_list=allowed_words_list, max_attempts=5):
    attempts = 0
    all_prior_texts = ''
    all_invalid_words = []
    message_history = []

    while attempts < max_attempts:
        main_prompt = generate_prompt(allowed_words_list, topic, all_prior_texts, ', '.join(all_invalid_words))
        system_prompt = system_prompt_template.format(allowed_words=','.join(allowed_words_list))
        
        message = anthropic_client.beta.tools.messages.create(
            model=BEST,
            max_tokens=1024,
            tools=[explanation_tool],
            system=system_prompt,
            messages=[{"role": "user", "content": [{"type": "text", "text": main_prompt}]}]
        )

        attempts += 1

        response = message.to_dict()
        
        output_data = next((data['input'] for data in response['content'] if 'input' in data), {})

        invalid_words = find_invalid_words(output_data['output'], allowed_words_list, topic.split(' '))

        output_data["invalid_words"] = invalid_words
        output_data["attempts"] = attempts
        pprint(output_data)

        message_history.append(output_data)

        if not invalid_words:
            return output_data['output']  # Return explanation if valid

        all_prior_texts = '\n'.join([entry['output'] for entry in message_history])
        all_invalid_words = sorted(set([word for entry in message_history for word in entry['invalid_words']] + invalid_words))

    raise Exception(f"Unable to generate a valid explanation for {topic} after {max_attempts} attempts.")


make_explanation("global warming", allowed_words_list,5)
