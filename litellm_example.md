Generic LLM tool use examples with litellm client using OpenAI GPT-4o via their API.

```bash
pip3 install litellm

export OPENAI_API_KEY="INSERT_KEY_HERE"
```

```python
import os
import litellm
from litellm import completion
from pydantic import BaseModel, Field
from typing import Literal

messages = [
    {"role": "user", "content": "What is the weather like in Boston?"}
]

class WeatherRequest(BaseModel):
    location: str = Field(..., description="The city and state, e.g. San Francisco, CA")
    unit: Literal["celsius", "fahrenheit"] = Field("fahrenheit")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": WeatherRequest.schema(),
        },
    }
]

openai_gpt = "openai/gpt-4o"
total_cost = 0

def track_cost_callback(
    kwargs,                 # kwargs to completion
    completion_response,    # response from completion
    start_time, end_time    # start/end time
):
    global total_cost
    try:
      response_cost = kwargs.get("response_cost", 0)
      print("response cost", response_cost)
      total_cost = total_cost + response_cost
      print("session cost", response_cost)
    except:
        pass

litellm.success_callback = [track_cost_callback]
response = completion(model=openai_gpt, messages=messages, tools=tools)

print(response)
print(response.choices[0].message.tool_calls[0].function.arguments)
```
