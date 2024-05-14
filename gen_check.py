from pprint import pprint
import traceback

from utils import llm_manager

from generation_schema_and_prompts import explanation_tool, explanation_system_prompt, generate_explanation_prompt, validate_explanation_output, extract_explanation_text, critique_system_prompt, generate_critique_prompt, extract_critique_score, critique_tool, validate_critique_output

def make_explanation(topic) -> str:
    context = {
        "topic": topic,
        "attempts": 0,
        "prior_texts": [],
        "invalid_words": []
    }
    while context["attempts"] < 3:
        try:
            user_prompt = generate_explanation_prompt(context)
            system_prompt_text = explanation_system_prompt()
            return llm_manager(
                user_prompt=user_prompt,
                system_prompt=system_prompt_text,
                tools=[{
                    "type": "function",
                    "function": explanation_tool
                }],
                extract_data=extract_explanation_text,
                validate_output=validate_explanation_output,
                context=context
            )

        except ValueError as e:
            
            traceback_response = traceback.format_exc()
            if "Invalid words found" in traceback_response:
                print('Invalid words found')
                continue
            print('context')
            pprint(context)
            print(traceback_response)
    raise Exception(f"Unable to generate a valid explanation for {context['topic']} after attempts.")

def review_and_score(explanation, topic):
    context = {
        "topic": topic,
        "explanation": explanation,
        "attempts": 0
    }
    while context["attempts"] < 2:
        try:
            user_prompt = generate_critique_prompt(context)
            system_prompt_text = critique_system_prompt()
            return llm_manager(
                user_prompt=user_prompt,
                system_prompt=system_prompt_text,
                tools=[{
                    "type": "function",
                    "function": critique_tool
                }],
                extract_data=extract_critique_score,
                validate_output=validate_critique_output,
                context=context
            )
        except Exception as e:
            print('context')
            pprint(context)
            print(traceback.format_exc())
    raise Exception(f"Unable to score the explanation for {context['topic']} after attempts.")

# Example usage

CANNED_EXPLANATION = "Global warming is when the world's weather becomes hot because of some actions by people. This can change how we live and the world around us."

explanation = make_explanation("global warming")


#explanation = CANNED_EXPLANATION

print("\nFinal explanation:", explanation)

result_review_and_score = review_and_score(explanation, "global warming")
print(f"\nScore and review for the explanation: {result_review_and_score}")
