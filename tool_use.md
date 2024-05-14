Generic LLM tool use examples with litellm, with Phi 3 via Ollama, and Groq via their API.

```bash
sudo docker run -it ubuntu:24.04
apt update && apt install -y python3.12-venv python3-pip curl
python3 -m venv myenv
source myenv/bin/activate

pip3 install litellm[proxy] litellm ipython

curl -fsSL https://ollama.com/install.sh | sh

ollama pull phi3
ollama serve &

litellm --model ollama/phi3 &

# export "GROQ_API_KEY"="INSERT_KEY_HERE"

```

```python
import os, litellm
from litellm import completion
from pydantic import BaseModel, Field
from typing import Literal


#litellm.add_function_to_prompt = True # may need to do this


messages = [
    {"role": "user", "content": "What is the weather like in Boston?"}
]

def get_current_weather(location):
  #if location == "Boston, MA":
  print(location)
  return "The weather is 12F"

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
GROQ = "groq/llama3-70b-8192"
LOCAL_PHI3 = "ollama/phi3"
#response = completion(model=LOCAL_PHI3, messages=messages, tools=tools)
response = completion(model=GROQ, messages=messages, tools=tools)

print(response)
print(response.choices[0].message.tool_calls[0].function.arguments)
```
