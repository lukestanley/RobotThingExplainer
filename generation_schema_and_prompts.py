import traceback
from words import find_invalid_words, allowed_words_list

explanation_schema = {
    "type": "object",
    "properties": {
        "planning": {
            "type": "string",
            "description": "Detailed planning of the explanation in a step-by-step manner. Share reflections on how to use the restricted word list to explain the topic. E.g: consider which words to use, how to structure the explanation, etc."
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

def explanation_system_prompt():
    allowed_word_list_string = ','.join(allowed_words_list)
    return f"""
    Use words from the allowed word list plus the term itself for providing explanation of requested terms. 
    Use good grammar. 
    
    These words are allowed: `{allowed_word_list_string}`, and also plural variations that have (s or es endings, "
        "e.g., `go` is in the list, but `goes` is allowed too, `car` is in the list, but `cars` is allowed too. "
        `animal` is in the list, so `animals` is allowed too - notice the pattern). "
    
    You must use the explanation_schema tool output format only, no markdown. 
    
    Use good English grammar! 
    Hint: Use very common words that young children can understand! 
    The text should sound normal as much as possible within the rules! 
    Do not use any other words!"""

def generate_explanation_prompt(context):
    allowed_word_list_string = ','.join(allowed_words_list)
    repair_info = ""
    if context["invalid_words"]:
        all_invalid_words = ', '.join(sorted(set(context["invalid_words"])))
        repair = f"These words were NOT allowed and caused past tries to fail: {all_invalid_words}. \nFix the sentences so it only uses allowed words. Use alternate words for the rejected words, as needed. WARNING: when introducing new terms, be sure that they are allowed or you will cause a failure! Reflect on the cause of the prior failure and how to avoid it."
        all_prior_texts = '\n'.join(context['prior_texts'])
        repair_info = f"Previous attempts failed so far:\n{all_prior_texts}\n{repair}\n"
    return f"""Provide explanations using the allowed word list: `{allowed_word_list_string}`.
    Explain the topic using `explanation_schema` using 2 sentences of explanation text.
    Provide a clear plan before delivering the final output, output JSON format only with the planning property and output property strings.
    For good grammar, appropriately use these symbols: `.`, `;`, `:`, `,`, `?`, and `'`.
    You can use some contractions. This is valid: `Good sun today; isn't it nice? Let's walk, and play: a great day!`
    This is the topic you need to explain: `{context['topic']}`.
    
    {repair_info}
    BE SURE TO ONLY USE THE ALLOWED WORDS AND THEIR PLURAL VARIATIONS, WITH GOOD GRAMMAR!"""

def validate_explanation_output(output, context):
    """ Default validation function to check if the output uses only allowed words. """
    invalid_words = find_invalid_words(output, allowed_words_list, context["topic"].split(' '))
    context['invalid_words'] = sorted(set(context["invalid_words"] + invalid_words))
    if invalid_words:
        raise ValueError(f"Invalid words found: {', '.join(invalid_words)}")
    return output

def extract_explanation_text(response, context):
    try:
        # Attempt to directly fetch the output text from the response
        output = next((data['input'] for data in response['content'] if 'input' in data), None)['output']
        print ('output:','\n',output)
        if output is None or not isinstance(output, str):
            print("Failed to extract valid output from response: %s", response)
            raise ValueError("Extracted data is invalid or not in the expected format.")
        context['prior_texts'].append(f"`{output}`\n") # Store the output for self-repair
        return output
    except Exception as e:
        print("Error extracting data: %s", traceback.format_exc())
        raise

def critique_system_prompt():
    return """You are an expert in evaluating explanations for clarity, simplicity, and effectiveness in conveying the core concepts to a general audience. Your task is to provide a numerical score between 1 and 5 for the given explanation, where:

1 - Poor explanation, fails to convey the core concepts, confusing or inaccurate
2 - Below average explanation, misses key points or lacks clarity
3 - Average explanation, covers the basics but could be improved
4 - Good explanation, clear and effective in conveying the main ideas
5 - Excellent explanation, highly effective in conveying the core concepts in a simple and engaging way

Please provide only the numerical score, without any additional text or explanation."""

def generate_critique_prompt(context):
    return f"""Score the following explanation for the topic "{context['topic']}" on a scale of 1 to 5:

`{context['explanation']}`
Please note that the explanation had to use only 2 sentences and words from a very restricted allowed list, bare this in mind when scoring.

"""

def extract_critique_score(response, context):
    try:
        score_str = response['content'][0]['text']
        score = int(score_str)
        if score < 1 or score > 5:
            raise ValueError(f"Invalid score: {score_str}")
        return score
    except Exception as e:
        print("Error extracting score: %s", traceback.format_exc())
        raise
