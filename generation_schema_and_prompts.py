import traceback
from pprint import pprint
from pydantic import BaseModel, Field

from words import find_invalid_words, allowed_words_list
from utils import get_tool_response_object_from_messages


class ExplanationSchema(BaseModel):
    planning: str = Field(..., description="Detailed planning of the explanation in a step-by-step manner. Share reflections on how to use the restricted word list to explain the topic. E.g: consider which words to use, how to structure the explanation, etc.")
    output: str = Field(..., description="Final explanation, adhering to the vocabulary list.")

class CritiqueSchema(BaseModel):
    review: str = Field(..., description="Reflect on the clarity and effectiveness of the explanation. Is the grammar using good English? Think step by step sharing detailed evaluation.")
    score: int = Field(..., description="A score between 1 and 5 evaluating the clarity and effectiveness of the explanation.")

explanation_tool = {
    "name": "explanation_schema",
    "description": "Show working out with a step-by-step plan for how to use the restricted word list to explain the topic.",
    "parameters": ExplanationSchema.schema(),
}

critique_tool = {
    "name": "critique_schema",
    "description": "Review the given explanation.",
    "parameters": CritiqueSchema.schema(),
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
        #print ('response:',response)
        output = None
        output_object = get_tool_response_object_from_messages(response)
        assert 'output' in output_object
        assert 'planning' in output_object
        output = output_object['output']
        if output is None or not isinstance(output, str):
            print("Failed to extract valid output from response: %s", response)
            raise ValueError("Extracted data is invalid or not in the expected format.")
        context['prior_texts'].append(f"`{output}`\n") # Store the output for self-repair
        return output
    except Exception as e:
        print("Error extracting data: %s", traceback.format_exc())
        raise

def critique_system_prompt():
    return """You are an expert in evaluating explanations for clarity, simplicity, and effectiveness in conveying the core concepts to a general audience and children.
Your task is to write a critical review and provide a numerical score between 1 and 5 for the given explanation using the critique_schema tool output format, where:

1 - Poor explanation, fails to convey the core concepts, confusing or inaccurate
2 - Below average explanation, misses key points or lacks clarity
3 - Average explanation, covers the basics but could be improved
4 - Good explanation, clear and effective in conveying the main ideas
5 - Excellent explanation, highly effective in conveying the core concepts in a simple and engaging way.

We need the written review to carefully consider the quality of the grammar too.
For example, should plural versions of the words have been used instead? Are there high frequency words that that are missing that would improve the grammar or make it easier to understand while being within the rules?
"""

def generate_critique_prompt(context):
    return f"""Score the following explanation for the topic "{context['topic']}" on a scale of 1 to 5 using the critique_schema tool output format:

`{context['explanation']}`

Please note that the explanation had to use ONLY 2 sentences and words from a very restricted allowed list, of about ~700 of the most frequent English words only! 
Here is the list used: `{','.join(allowed_words_list)}`.

Bare in mind the rules the author had to comply with when reviewing it and scoring, especially when making suggestions for improvement.
"""

def validate_critique_output(output, context):
    """ Default validation function to check if the output is a valid integer score. """
    try:
        score = output["score"]
        if score < 1 or score > 5:
            raise ValueError(f"Invalid score: {score}")
        return output
    except Exception as e:
        print("Error validating critique output: %s", traceback.format_exc())
        raise


def extract_critique_score(response, context):
    try:
        output = None
        output = get_tool_response_object_from_messages(response)
        assert 'score' in output

        if output is None or not isinstance(output, dict):
            print("Failed to extract valid output from response: %s", response)
            raise ValueError("Extracted data is invalid or not in the expected format.")
        return output
    except Exception as e:
        print("Error extracting score: %s", traceback.format_exc())
        raise
