
import json

from litellm import completion

# Definitions for interaction with a Large Language Model
BEST_MODEL = "openai/gpt-4o"

def llm_manager(user_prompt, system_prompt, tools, extract_data, validate_output, context, max_tokens = 3000):
    """ Manages sending prompts to the LLM and handles the response using the provided functions. If validation fails, it raises an exception. """
    print('starting request')
    response = completion(
        model=BEST_MODEL,
        max_tokens=max_tokens,
        tools=tools,
        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
    )
    print('got a response')
    context["attempts"] += 1
    output = extract_data(response, context)
    
    return validate_output(output, context)

def get_tool_response_object_from_messages(response):
    """Extracts the tool response object from the LLM response message.

    Handles responses with nested structures and those containing JSON content.

    Args:
        response (ModelResponse): The response from the LLM.

    Returns:
        dict: Parsed JSON object from the response.

    Raises:
        AttributeError: If no tool_calls or valid content found in the response.
        ValueError: If JSON decoding fails.
    """
    output_json_string = None

    for choice in response.choices:
        # Check for tool_calls in the response
        if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
            for call in choice.message.tool_calls:
                if hasattr(call.function, 'arguments'):
                    output_json_string = call.function.arguments
                    break
        # Check if content exists and try to parse it as JSON
        elif hasattr(choice.message, 'content') and choice.message.content:
            try:
                content_json = json.loads(choice.message.content)
                if 'tool_uses' in content_json:
                    for tool_use in content_json['tool_uses']:
                        if 'parameters' in tool_use:
                            output_json_string = json.dumps(tool_use['parameters'])
                            break
            except json.JSONDecodeError:
                print("Failed to decode JSON content: %s" % choice.message.content)
                continue

        if output_json_string:
            break

    if not output_json_string:
        raise AttributeError('No tool_calls or valid content found in the response.')

    # Convert the JSON string to a dictionary and return it
    try:
        output_object = json.loads(output_json_string)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to decode output_json_string: {output_json_string}")

    return output_object
