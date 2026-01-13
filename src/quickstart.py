#%% [markdown]
# # LangGraph Quickstart with AI71 Foundry
#
# This notebook demonstrates the LangGraph quickstart example using AI71 Foundry
# with Claude Sonnet 4.5 (via OpenAI-compatible API).



print("1")


# %%

# %%

# %%

# %%

#%% Setup - Load environment and imports
import os

from dotenv import load_dotenv
#%%
# Load environment variables from .env file
load_dotenv()

#%%
import dotenv



#%%
# Verify environment is set up
print(f"API Base: {os.getenv('OPENAI_API_BASE')}")
print(f"API Key set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")

# %% Import LangGraph and LangChain components
from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
# from langgraph import tool
from langchain.tools import tool

#%%

model1=ChatOpenAI(
    model="anthropic/claude-sonnet-4-5",  # Claude Sonnet 4.5 via Foundry
    base_url=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY")
)

model1.invoke([{"role":"user","content":"Hello!"}])
#%%
print(os.getenv("OPENAI_API_BASE"))
print(os.getenv("OPENAI_API_KEY"))

# %% Define the state schema
# State holds the conversation messages
class State(TypedDict):
    messages: Annotated[list, add_messages]

# %% Initialize the model with AI71 Foundry
# Using OpenAI-compatible API with Claude Sonnet 4.5
model = ChatOpenAI(
    model="anthropic/claude-sonnet-4-5",  # Claude Sonnet 4.5 via Foundry
    base_url=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7,
    max_tokens=1000,
)

print(f"Model initialized: {model.model_name}")

# %% Define a simple tool
# @tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

# Bind the tool to the model
tools = [get_weather]
model_with_tools = model.bind_tools(tools)

# %% Define the chatbot node
def chatbot(state: State):
    """Process messages and generate a response."""
    return {"messages": [model_with_tools.invoke(state["messages"])]}

# %% Define tool execution node
import json
from langchain_core.messages import ToolMessage

#%%

def tool_node(state: State):
    """Execute tool calls from the model."""
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        # Execute the appropriate tool
        if tool_name == "get_weather":
            result = get_weather(**tool_args)
        else:
            result = f"Unknown tool: {tool_name}"

        outputs.append(
            ToolMessage(
                content=json.dumps(result),
                name=tool_name,
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}

# %% Define routing logic
def should_continue(state: State):
    """Determine whether to continue to tools or end."""
    messages = state["messages"]
    # So this implicitly just checks the last message and figures out if there are any two calls in that last message. If there are, it means that they should be executed before the final response is created, and we are not at the final response yet. 
    last_message = messages[-1]
    # If the LLM makes a tool call, route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, end the conversation And assume that now, in the final state, we have the final response as the content of the last message. 
    return END

# %% Build the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

# Add edges
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", should_continue)
graph_builder.add_edge("tools", "chatbot")

# Set up memory for conversation persistence
memory = MemorySaver()

# Compile the graph
graph = graph_builder.compile(checkpointer=memory)

print("Graph compiled successfully!")

# %% Visualize the graph (optional - requires graphviz)
try:
    from IPython.display import Image, display
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception as e:
    print(f"Could not display graph visualization: {e}")
    print("\nGraph structure:")
    print("START -> chatbot -> (tools -> chatbot | END)")

# %% Test the chatbot - Simple greeting
config = {"configurable": {"thread_id": "1"}}

# First message
response = graph.invoke(
    {"messages": [{"role": "user", "content": "Hello! How are you?"}]},
    config=config
)

print("User: Hello! How are you?")
print(f"Assistant: {response['messages'][-1].content}")

# %% Test the chatbot - Weather query (uses tool)
response = graph.invoke(
    {"messages": [{"role": "user", "content": "What's the weather like in San Francisco?"}]},
    config=config
)

print("\nUser: What's the weather like in San Francisco?")
print(f"Assistant: {response['messages'][-1].content}")

# %% Test conversation memory
# Continue the same thread - the model should remember previous context
response = graph.invoke(
    {"messages": [{"role": "user", "content": "What about in Dubai?"}]},
    config=config
)

print("\nUser: What about in Dubai?")
print(f"Assistant: {response['messages'][-1].content}")

# %% Start a new conversation thread
config_new = {"configurable": {"thread_id": "2"}}

response = graph.invoke(
    {"messages": [{"role": "user", "content": "Can you tell me a joke?"}]},
    config=config_new
)

print("\n--- New Thread ---")
print("User: Can you tell me a joke?")
print(f"Assistant: {response['messages'][-1].content}")

# %% Summary
print("\n" + "="*50)
print("SUMMARY")
print("="*50)
print("""
This quickstart demonstrated:
1. Setting up LangGraph with AI71 Foundry (OpenAI-compatible API)
2. Using Claude Sonnet 4.5 as the language model
3. Creating a simple tool (get_weather)
4. Building a stateful graph with:
   - Chatbot node for generating responses
   - Tool node for executing function calls
   - Conditional routing based on tool calls
5. Using MemorySaver for conversation persistence
6. Running multiple conversation threads

Key configuration:
- API Base: https://foundry71.ai71.ai/v1
- Model: anthropic/claude-sonnet-4-5
""")
