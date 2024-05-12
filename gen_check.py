from pprint import pprint
import traceback
import anthropic
from generation_schema_and_prompts import explanation_schema, explanation_tool, explanation_system_prompt, generate_explanation_prompt, validate_explanation_output, extract_explanation_text, critique_system_prompt, generate_critique_prompt, extract_critique_score

# Definitions for interaction with a Large Language Model
anthropic_client = anthropic.Anthropic()
BEST_MODEL = "claude-3-sonnet-20240229"
FAST_MODEL = "claude-3-haiku-20240307"


def llm_manager(user_prompt, system_prompt, tools, extract_data, validate_output, context, max_tokens = 3000):
    """ Manages sending prompts to the LLM and handles the response using the provided functions. If validation fails, it raises an exception. """
    response = anthropic_client.beta.tools.messages.create(
        model=BEST_MODEL,
        max_tokens=max_tokens,
        tools=tools,
        system=system_prompt,
        messages=[{"role": "user", "content": [{"type": "text", "text": user_prompt}]}]
    ).to_dict()
    context["attempts"] += 1
    output = extract_data(response, context)
    
    return validate_output(output, context)

def make_explanation(topic) -> str:
    context = {
        "topic": topic,
        "attempts": 0,
        "prior_texts": [],
        "invalid_words": []
    }
    while context["attempts"] < 5:
        try:
            user_prompt = generate_explanation_prompt(context)
            system_prompt_text = explanation_system_prompt()
            # Returns the valid explanation if successful
            return llm_manager(
                user_prompt=user_prompt, 
                system_prompt=system_prompt_text, 
                tools= [explanation_tool], 
                extract_data=extract_explanation_text, 
                validate_output=validate_explanation_output, 
                context=context
            )

        except ValueError as e:
            
            print('context')
            pprint(context)
            print(traceback.format_exc())
    raise Exception(f"Unable to generate a valid explanation for {context['topic']} after 5 attempts.")

def score_explanation(explanation, topic):
    context = {
        "topic": topic,
        "explanation": explanation,
        "attempts": 0
    }
    while context["attempts"] < 5:
        try:
            user_prompt = generate_critique_prompt(context)
            system_prompt_text = critique_system_prompt()
            return llm_manager(
                user_prompt=user_prompt,
                system_prompt=system_prompt_text,
                tools=[],
                extract_data=extract_critique_score,
                validate_output=lambda x, _: x,  # No validation needed
                context=context
            )
        except Exception as e:
            print('context')
            pprint(context)
            print(traceback.format_exc())
    raise Exception(f"Unable to score the explanation for {context['topic']} after 5 attempts.")

# Example usage

explanation = make_explanation("global warming")
print("\nFinal explanation:", explanation)

score = score_explanation(explanation, "global warming")
print(f"\nScore for the explanation: {score}")
