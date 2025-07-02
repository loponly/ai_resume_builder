Tools¶
What is a Tool?¶
In the context of ADK, a Tool represents a specific capability provided to an AI agent, enabling it to perform actions and interact with the world beyond its core text generation and reasoning abilities. What distinguishes capable agents from basic language models is often their effective use of tools.

Technically, a tool is typically a modular code component—like a Python/ Java function, a class method, or even another specialized agent—designed to execute a distinct, predefined task. These tasks often involve interacting with external systems or data.

Agent tool call

Key Characteristics¶
Action-Oriented: Tools perform specific actions, such as:

Querying databases
Making API requests (e.g., fetching weather data, booking systems)
Searching the web
Executing code snippets
Retrieving information from documents (RAG)
Interacting with other software or services
Extends Agent capabilities: They empower agents to access real-time information, affect external systems, and overcome the knowledge limitations inherent in their training data.

Execute predefined logic: Crucially, tools execute specific, developer-defined logic. They do not possess their own independent reasoning capabilities like the agent's core Large Language Model (LLM). The LLM reasons about which tool to use, when, and with what inputs, but the tool itself just executes its designated function.

How Agents Use Tools¶
Agents leverage tools dynamically through mechanisms often involving function calling. The process generally follows these steps:

Reasoning: The agent's LLM analyzes its system instruction, conversation history, and user request.
Selection: Based on the analysis, the LLM decides on which tool, if any, to execute, based on the tools available to the agent and the docstrings that describes each tool.
Invocation: The LLM generates the required arguments (inputs) for the selected tool and triggers its execution.
Observation: The agent receives the output (result) returned by the tool.
Finalization: The agent incorporates the tool's output into its ongoing reasoning process to formulate the next response, decide the subsequent step, or determine if the goal has been achieved.
Think of the tools as a specialized toolkit that the agent's intelligent core (the LLM) can access and utilize as needed to accomplish complex tasks.

Tool Types in ADK¶
ADK offers flexibility by supporting several types of tools:

Function Tools: Tools created by you, tailored to your specific application's needs.
Functions/Methods: Define standard synchronous functions or methods in your code (e.g., Python def).
Agents-as-Tools: Use another, potentially specialized, agent as a tool for a parent agent.
Long Running Function Tools: Support for tools that perform asynchronous operations or take significant time to complete.
Built-in Tools: Ready-to-use tools provided by the framework for common tasks. Examples: Google Search, Code Execution, Retrieval-Augmented Generation (RAG).
Third-Party Tools: Integrate tools seamlessly from popular external libraries. Examples: LangChain Tools, CrewAI Tools.
Navigate to the respective documentation pages linked above for detailed information and examples for each tool type.

Referencing Tool in Agent’s Instructions¶
Within an agent's instructions, you can directly reference a tool by using its function name. If the tool's function name and docstring are sufficiently descriptive, your instructions can primarily focus on when the Large Language Model (LLM) should utilize the tool. This promotes clarity and helps the model understand the intended use of each tool.

It is crucial to clearly instruct the agent on how to handle different return values that a tool might produce. For example, if a tool returns an error message, your instructions should specify whether the agent should retry the operation, give up on the task, or request additional information from the user.

Furthermore, ADK supports the sequential use of tools, where the output of one tool can serve as the input for another. When implementing such workflows, it's important to describe the intended sequence of tool usage within the agent's instructions to guide the model through the necessary steps.

Example¶
The following example showcases how an agent can use tools by referencing their function names in its instructions. It also demonstrates how to guide the agent to handle different return values from tools, such as success or error messages, and how to orchestrate the sequential use of multiple tools to accomplish a task.


Python
Java

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

APP_NAME="weather_sentiment_agent"
USER_ID="user1234"
SESSION_ID="1234"
MODEL_ID="gemini-2.0-flash"

# Tool 1
def get_weather_report(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Returns:
        dict: A dictionary containing the weather information with a 'status' key ('success' or 'error') and a 'report' key with the weather details if successful, or an 'error_message' if an error occurred.
    """
    if city.lower() == "london":
        return {"status": "success", "report": "The current weather in London is cloudy with a temperature of 18 degrees Celsius and a chance of rain."}
    elif city.lower() == "paris":
        return {"status": "success", "report": "The weather in Paris is sunny with a temperature of 25 degrees Celsius."}
    else:
        return {"status": "error", "error_message": f"Weather information for '{city}' is not available."}

weather_tool = FunctionTool(func=get_weather_report)


# Tool 2
def analyze_sentiment(text: str) -> dict:
    """Analyzes the sentiment of the given text.

    Returns:
        dict: A dictionary with 'sentiment' ('positive', 'negative', or 'neutral') and a 'confidence' score.
    """
    if "good" in text.lower() or "sunny" in text.lower():
        return {"sentiment": "positive", "confidence": 0.8}
    elif "rain" in text.lower() or "bad" in text.lower():
        return {"sentiment": "negative", "confidence": 0.7}
    else:
        return {"sentiment": "neutral", "confidence": 0.6}

sentiment_tool = FunctionTool(func=analyze_sentiment)


# Agent
weather_sentiment_agent = Agent(
    model=MODEL_ID,
    name='weather_sentiment_agent',
    instruction="""You are a helpful assistant that provides weather information and analyzes the sentiment of user feedback.
**If the user asks about the weather in a specific city, use the 'get_weather_report' tool to retrieve the weather details.**
**If the 'get_weather_report' tool returns a 'success' status, provide the weather report to the user.**
**If the 'get_weather_report' tool returns an 'error' status, inform the user that the weather information for the specified city is not available and ask if they have another city in mind.**
**After providing a weather report, if the user gives feedback on the weather (e.g., 'That's good' or 'I don't like rain'), use the 'analyze_sentiment' tool to understand their sentiment.** Then, briefly acknowledge their sentiment.
You can handle these tasks sequentially if needed.""",
    tools=[weather_tool, sentiment_tool]
)

# Session and Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=weather_sentiment_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner


# Agent Interaction
async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)

# Note: In Colab, you can directly use 'await' at the top level.
# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
await call_agent_async("weather in london?")

Tool Context¶
For more advanced scenarios, ADK allows you to access additional contextual information within your tool function by including the special parameter tool_context: ToolContext. By including this in the function signature, ADK will automatically provide an instance of the ToolContext class when your tool is called during agent execution.

The ToolContext provides access to several key pieces of information and control levers:

state: State: Read and modify the current session's state. Changes made here are tracked and persisted.

actions: EventActions: Influence the agent's subsequent actions after the tool runs (e.g., skip summarization, transfer to another agent).

function_call_id: str: The unique identifier assigned by the framework to this specific invocation of the tool. Useful for tracking and correlating with authentication responses. This can also be helpful when multiple tools are called within a single model response.

function_call_event_id: str: This attribute provides the unique identifier of the event that triggered the current tool call. This can be useful for tracking and logging purposes.

auth_response: Any: Contains the authentication response/credentials if an authentication flow was completed before this tool call.

Access to Services: Methods to interact with configured services like Artifacts and Memory.

Note that you shouldn't include the tool_context parameter in the tool function docstring. Since ToolContext is automatically injected by the ADK framework after the LLM decides to call the tool function, it is not relevant for the LLM's decision-making and including it can confuse the LLM.

State Management¶
The tool_context.state attribute provides direct read and write access to the state associated with the current session. It behaves like a dictionary but ensures that any modifications are tracked as deltas and persisted by the session service. This enables tools to maintain and share information across different interactions and agent steps.

Reading State: Use standard dictionary access (tool_context.state['my_key']) or the .get() method (tool_context.state.get('my_key', default_value)).

Writing State: Assign values directly (tool_context.state['new_key'] = 'new_value'). These changes are recorded in the state_delta of the resulting event.

State Prefixes: Remember the standard state prefixes:

app:*: Shared across all users of the application.

user:*: Specific to the current user across all their sessions.

(No prefix): Specific to the current session.

temp:*: Temporary, not persisted across invocations (useful for passing data within a single run call but generally less useful inside a tool context which operates between LLM calls).


Python
Java

from google.adk.tools import ToolContext, FunctionTool

def update_user_preference(preference: str, value: str, tool_context: ToolContext):
    """Updates a user-specific preference."""
    user_prefs_key = "user:preferences"
    # Get current preferences or initialize if none exist
    preferences = tool_context.state.get(user_prefs_key, {})
    preferences[preference] = value
    # Write the updated dictionary back to the state
    tool_context.state[user_prefs_key] = preferences
    print(f"Tool: Updated user preference '{preference}' to '{value}'")
    return {"status": "success", "updated_preference": preference}

pref_tool = FunctionTool(func=update_user_preference)

# In an Agent:
# my_agent = Agent(..., tools=[pref_tool])

# When the LLM calls update_user_preference(preference='theme', value='dark', ...):
# The tool_context.state will be updated, and the change will be part of the
# resulting tool response event's actions.state_delta.

Controlling Agent Flow¶
The tool_context.actions attribute (ToolContext.actions() in Java) holds an EventActions object. Modifying attributes on this object allows your tool to influence what the agent or framework does after the tool finishes execution.

skip_summarization: bool: (Default: False) If set to True, instructs the ADK to bypass the LLM call that typically summarizes the tool's output. This is useful if your tool's return value is already a user-ready message.

transfer_to_agent: str: Set this to the name of another agent. The framework will halt the current agent's execution and transfer control of the conversation to the specified agent. This allows tools to dynamically hand off tasks to more specialized agents.

escalate: bool: (Default: False) Setting this to True signals that the current agent cannot handle the request and should pass control up to its parent agent (if in a hierarchy). In a LoopAgent, setting escalate=True in a sub-agent's tool will terminate the loop.

Example¶

Python
Java

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.genai import types

APP_NAME="customer_support_agent"
USER_ID="user1234"
SESSION_ID="1234"


def check_and_transfer(query: str, tool_context: ToolContext) -> str:
    """Checks if the query requires escalation and transfers to another agent if needed."""
    if "urgent" in query.lower():
        print("Tool: Detected urgency, transferring to the support agent.")
        tool_context.actions.transfer_to_agent = "support_agent"
        return "Transferring to the support agent..."
    else:
        return f"Processed query: '{query}'. No further action needed."

escalation_tool = FunctionTool(func=check_and_transfer)

main_agent = Agent(
    model='gemini-2.0-flash',
    name='main_agent',
    instruction="""You are the first point of contact for customer support of an analytics tool. Answer general queries. If the user indicates urgency, use the 'check_and_transfer' tool.""",
    tools=[check_and_transfer]
)

support_agent = Agent(
    model='gemini-2.0-flash',
    name='support_agent',
    instruction="""You are the dedicated support agent. Mentioned you are a support handler and please help the user with their urgent issue."""
)

main_agent.sub_agents = [support_agent]

# Session and Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=main_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner

# Agent Interaction
async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)

# Note: In Colab, you can directly use 'await' at the top level.
# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
await call_agent_async("this is urgent, i cant login")

Explanation¶
We define two agents: main_agent and support_agent. The main_agent is designed to be the initial point of contact.
The check_and_transfer tool, when called by main_agent, examines the user's query.
If the query contains the word "urgent", the tool accesses the tool_context, specifically tool_context.actions, and sets the transfer_to_agent attribute to support_agent.
This action signals to the framework to transfer the control of the conversation to the agent named support_agent.
When the main_agent processes the urgent query, the check_and_transfer tool triggers the transfer. The subsequent response would ideally come from the support_agent.
For a normal query without urgency, the tool simply processes it without triggering a transfer.
This example illustrates how a tool, through EventActions in its ToolContext, can dynamically influence the flow of the conversation by transferring control to another specialized agent.

Authentication¶
python_only

ToolContext provides mechanisms for tools interacting with authenticated APIs. If your tool needs to handle authentication, you might use the following:

auth_response: Contains credentials (e.g., a token) if authentication was already handled by the framework before your tool was called (common with RestApiTool and OpenAPI security schemes).

request_credential(auth_config: dict): Call this method if your tool determines authentication is needed but credentials aren't available. This signals the framework to start an authentication flow based on the provided auth_config.

get_auth_response(): Call this in a subsequent invocation (after request_credential was successfully handled) to retrieve the credentials the user provided.

For detailed explanations of authentication flows, configuration, and examples, please refer to the dedicated Tool Authentication documentation page.

Context-Aware Data Access Methods¶
These methods provide convenient ways for your tool to interact with persistent data associated with the session or user, managed by configured services.

list_artifacts() (or listArtifacts() in Java): Returns a list of filenames (or keys) for all artifacts currently stored for the session via the artifact_service. Artifacts are typically files (images, documents, etc.) uploaded by the user or generated by tools/agents.

load_artifact(filename: str): Retrieves a specific artifact by its filename from the artifact_service. You can optionally specify a version; if omitted, the latest version is returned. Returns a google.genai.types.Part object containing the artifact data and mime type, or None if not found.

save_artifact(filename: str, artifact: types.Part): Saves a new version of an artifact to the artifact_service. Returns the new version number (starting from 0).

search_memory(query: str) python_only

Queries the user's long-term memory using the configured memory_service. This is useful for retrieving relevant information from past interactions or stored knowledge. The structure of the SearchMemoryResponse depends on the specific memory service implementation but typically contains relevant text snippets or conversation excerpts.

Example¶

Python
Java

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.tools import ToolContext, FunctionTool
from google.genai import types


def process_document(
    document_name: str, analysis_query: str, tool_context: ToolContext
) -> dict:
    """Analyzes a document using context from memory."""

    # 1. Load the artifact
    print(f"Tool: Attempting to load artifact: {document_name}")
    document_part = tool_context.load_artifact(document_name)

    if not document_part:
        return {"status": "error", "message": f"Document '{document_name}' not found."}

    document_text = document_part.text  # Assuming it's text for simplicity
    print(f"Tool: Loaded document '{document_name}' ({len(document_text)} chars).")

    # 2. Search memory for related context
    print(f"Tool: Searching memory for context related to: '{analysis_query}'")
    memory_response = tool_context.search_memory(
        f"Context for analyzing document about {analysis_query}"
    )
    memory_context = "\n".join(
        [
            m.events[0].content.parts[0].text
            for m in memory_response.memories
            if m.events and m.events[0].content
        ]
    )  # Simplified extraction
    print(f"Tool: Found memory context: {memory_context[:100]}...")

    # 3. Perform analysis (placeholder)
    analysis_result = f"Analysis of '{document_name}' regarding '{analysis_query}' using memory context: [Placeholder Analysis Result]"
    print("Tool: Performed analysis.")

    # 4. Save the analysis result as a new artifact
    analysis_part = types.Part.from_text(text=analysis_result)
    new_artifact_name = f"analysis_{document_name}"
    version = await tool_context.save_artifact(new_artifact_name, analysis_part)
    print(f"Tool: Saved analysis result as '{new_artifact_name}' version {version}.")

    return {
        "status": "success",
        "analysis_artifact": new_artifact_name,
        "version": version,
    }


doc_analysis_tool = FunctionTool(func=process_document)

# In an Agent:
# Assume artifact 'report.txt' was previously saved.
# Assume memory service is configured and has relevant past data.
# my_agent = Agent(..., tools=[doc_analysis_tool], artifact_service=..., memory_service=...)

By leveraging the ToolContext, developers can create more sophisticated and context-aware custom tools that seamlessly integrate with ADK's architecture and enhance the overall capabilities of their agents.

Defining Effective Tool Functions¶
When using a method or function as an ADK Tool, how you define it significantly impacts the agent's ability to use it correctly. The agent's Large Language Model (LLM) relies heavily on the function's name, parameters (arguments), type hints, and docstring / source code comments to understand its purpose and generate the correct call.

Here are key guidelines for defining effective tool functions:

Function Name:

Use descriptive, verb-noun based names that clearly indicate the action (e.g., get_weather, searchDocuments, schedule_meeting).
Avoid generic names like run, process, handle_data, or overly ambiguous names like doStuff. Even with a good description, a name like do_stuff might confuse the model about when to use the tool versus, for example, cancelFlight.
The LLM uses the function name as a primary identifier during tool selection.
Parameters (Arguments):

Your function can have any number of parameters.
Use clear and descriptive names (e.g., city instead of c, search_query instead of q).
Provide type hints in Python for all parameters (e.g., city: str, user_id: int, items: list[str]). This is essential for ADK to generate the correct schema for the LLM.
Ensure all parameter types are JSON serializable. All java primitives as well as standard Python types like str, int, float, bool, list, dict, and their combinations are generally safe. Avoid complex custom class instances as direct parameters unless they have a clear JSON representation.
Do not set default values for parameters. E.g., def my_func(param1: str = "default"). Default values are not reliably supported or used by the underlying models during function call generation. All necessary information should be derived by the LLM from the context or explicitly requested if missing.
self / cls Handled Automatically: Implicit parameters like self (for instance methods) or cls (for class methods) are automatically handled by ADK and excluded from the schema shown to the LLM. You only need to define type hints and descriptions for the logical parameters your tool requires the LLM to provide.
Return Type:

The function's return value must be a dictionary (dict) in Python or a Map in Java.
If your function returns a non-dictionary type (e.g., a string, number, list), the ADK framework will automatically wrap it into a dictionary/Map like {'result': your_original_return_value} before passing the result back to the model.
Design the dictionary/Map keys and values to be descriptive and easily understood by the LLM. Remember, the model reads this output to decide its next step.
Include meaningful keys. For example, instead of returning just an error code like 500, return {'status': 'error', 'error_message': 'Database connection failed'}.
It's a highly recommended practice to include a status key (e.g., 'success', 'error', 'pending', 'ambiguous') to clearly indicate the outcome of the tool execution for the model.
Docstring / Source Code Comments:

This is critical. The docstring is the primary source of descriptive information for the LLM.
Clearly state what the tool does. Be specific about its purpose and limitations.
Explain when the tool should be used. Provide context or example scenarios to guide the LLM's decision-making.
Describe each parameter clearly. Explain what information the LLM needs to provide for that argument.
Describe the structure and meaning of the expected dict return value, especially the different status values and associated data keys.
Do not describe the injected ToolContext parameter. Avoid mentioning the optional tool_context: ToolContext parameter within the docstring description since it is not a parameter the LLM needs to know about. ToolContext is injected by ADK, after the LLM decides to call it.
Example of a good definition:


Python
Java

def lookup_order_status(order_id: str) -> dict:
  """Fetches the current status of a customer's order using its ID.

  Use this tool ONLY when a user explicitly asks for the status of
  a specific order and provides the order ID. Do not use it for
  general inquiries.

  Args:
      order_id: The unique identifier of the order to look up.

  Returns:
      A dictionary containing the order status.
      Possible statuses: 'shipped', 'processing', 'pending', 'error'.
      Example success: {'status': 'shipped', 'tracking_number': '1Z9...'}
      Example error: {'status': 'error', 'error_message': 'Order ID not found.'}
  """
  # ... function implementation to fetch status ...
  if status := fetch_status_from_backend(order_id):
       return {"status": status.state, "tracking_number": status.tracking} # Example structure
  else:
       return {"status": "error", "error_message": f"Order ID {order_id} not found."}

Simplicity and Focus:
Keep Tools Focused: Each tool should ideally perform one well-defined task.
Fewer Parameters are Better: Models generally handle tools with fewer, clearly defined parameters more reliably than those with many optional or complex ones.
Use Simple Data Types: Prefer basic types (str, int, bool, float, List[str], in Python, or int, byte, short, long, float, double, boolean and char in Java) over complex custom classes or deeply nested structures as parameters when possible.
Decompose Complex Tasks: Break down functions that perform multiple distinct logical steps into smaller, more focused tools. For instance, instead of a single update_user_profile(profile: ProfileObject) tool, consider separate tools like update_user_name(name: str), update_user_address(address: str), update_user_preferences(preferences: list[str]), etc. This makes it easier for the LLM to select and use the correct capability.
By adhering to these guidelines, you provide the LLM with the clarity and structure it needs to effectively utilize your custom function tools, leading to more capable and reliable agent behavior.

Toolsets: Grouping and Dynamically Providing Tools python_only¶
Beyond individual tools, ADK introduces the concept of a Toolset via the BaseToolset interface (defined in google.adk.tools.base_toolset). A toolset allows you to manage and provide a collection of BaseTool instances, often dynamically, to an agent.

This approach is beneficial for:

Organizing Related Tools: Grouping tools that serve a common purpose (e.g., all tools for mathematical operations, or all tools interacting with a specific API).
Dynamic Tool Availability: Enabling an agent to have different tools available based on the current context (e.g., user permissions, session state, or other runtime conditions). The get_tools method of a toolset can decide which tools to expose.
Integrating External Tool Providers: Toolsets can act as adapters for tools coming from external systems, like an OpenAPI specification or an MCP server, converting them into ADK-compatible BaseTool objects.
The BaseToolset Interface¶
Any class acting as a toolset in ADK should implement the BaseToolset abstract base class. This interface primarily defines two methods:

async def get_tools(...) -> list[BaseTool]: This is the core method of a toolset. When an ADK agent needs to know its available tools, it will call get_tools() on each BaseToolset instance provided in its tools list.

It receives an optional readonly_context (an instance of ReadonlyContext). This context provides read-only access to information like the current session state (readonly_context.state), agent name, and invocation ID. The toolset can use this context to dynamically decide which tools to return.
It must return a list of BaseTool instances (e.g., FunctionTool, RestApiTool).
async def close(self) -> None: This asynchronous method is called by the ADK framework when the toolset is no longer needed, for example, when an agent server is shutting down or the Runner is being closed. Implement this method to perform any necessary cleanup, such as closing network connections, releasing file handles, or cleaning up other resources managed by the toolset.

Using Toolsets with Agents¶
You can include instances of your BaseToolset implementations directly in an LlmAgent's tools list, alongside individual BaseTool instances.

When the agent initializes or needs to determine its available capabilities, the ADK framework will iterate through the tools list:

If an item is a BaseTool instance, it's used directly.
If an item is a BaseToolset instance, its get_tools() method is called (with the current ReadonlyContext), and the returned list of BaseTools is added to the agent's available tools.
Example: A Simple Math Toolset¶
Let's create a basic example of a toolset that provides simple arithmetic operations.


# 1. Define the individual tool functions
def add_numbers(a: int, b: int, tool_context: ToolContext) -> Dict[str, Any]:
    """Adds two integer numbers.
    Args:
        a: The first number.
        b: The second number.
    Returns:
        A dictionary with the sum, e.g., {'status': 'success', 'result': 5}
    """
    print(f"Tool: add_numbers called with a={a}, b={b}")
    result = a + b
    # Example: Storing something in tool_context state
    tool_context.state["last_math_operation"] = "addition"
    return {"status": "success", "result": result}


def subtract_numbers(a: int, b: int) -> Dict[str, Any]:
    """Subtracts the second number from the first.
    Args:
        a: The first number.
        b: The second number.
    Returns:
        A dictionary with the difference, e.g., {'status': 'success', 'result': 1}
    """
    print(f"Tool: subtract_numbers called with a={a}, b={b}")
    return {"status": "success", "result": a - b}


# 2. Create the Toolset by implementing BaseToolset
class SimpleMathToolset(BaseToolset):
    def __init__(self, prefix: str = "math_"):
        self.prefix = prefix
        # Create FunctionTool instances once
        self._add_tool = FunctionTool(
            func=add_numbers,
            name=f"{self.prefix}add_numbers",  # Toolset can customize names
        )
        self._subtract_tool = FunctionTool(
            func=subtract_numbers, name=f"{self.prefix}subtract_numbers"
        )
        print(f"SimpleMathToolset initialized with prefix '{self.prefix}'")

    async def get_tools(
        self, readonly_context: Optional[ReadonlyContext] = None
    ) -> List[BaseTool]:
        print(f"SimpleMathToolset.get_tools() called.")
        # Example of dynamic behavior:
        # Could use readonly_context.state to decide which tools to return
        # For instance, if readonly_context.state.get("enable_advanced_math"):
        #    return [self._add_tool, self._subtract_tool, self._multiply_tool]

        # For this simple example, always return both tools
        tools_to_return = [self._add_tool, self._subtract_tool]
        print(f"SimpleMathToolset providing tools: {[t.name for t in tools_to_return]}")
        return tools_to_return

    async def close(self) -> None:
        # No resources to clean up in this simple example
        print(f"SimpleMathToolset.close() called for prefix '{self.prefix}'.")
        await asyncio.sleep(0)  # Placeholder for async cleanup if needed


# 3. Define an individual tool (not part of the toolset)
def greet_user(name: str = "User") -> Dict[str, str]:
    """Greets the user."""
    print(f"Tool: greet_user called with name={name}")
    return {"greeting": f"Hello, {name}!"}


greet_tool = FunctionTool(func=greet_user)

# 4. Instantiate the toolset
math_toolset_instance = SimpleMathToolset(prefix="calculator_")

# 5. Define an agent that uses both the individual tool and the toolset
calculator_agent = LlmAgent(
    name="CalculatorAgent",
    model="gemini-2.0-flash",  # Replace with your desired model
    instruction="You are a helpful calculator and greeter. "
    "Use 'greet_user' for greetings. "
    "Use 'calculator_add_numbers' to add and 'calculator_subtract_numbers' to subtract. "
    "Announce the state of 'last_math_operation' if it's set.",
    tools=[greet_tool, math_toolset_instance],  # Individual tool  # Toolset instance
)
In this example:

SimpleMathToolset implements BaseToolset and its get_tools() method returns FunctionTool instances for add_numbers and subtract_numbers. It also customizes their names using a prefix.
The calculator_agent is configured with both an individual greet_tool and an instance of SimpleMathToolset.
When calculator_agent is run, ADK will call math_toolset_instance.get_tools(). The agent's LLM will then have access to greet_user, calculator_add_numbers, and calculator_subtract_numbers to handle user requests.
The add_numbers tool demonstrates writing to tool_context.state, and the agent's instruction mentions reading this state.
The close() method is called to ensure any resources held by the toolset are released.
Toolsets offer a powerful way to organize, manage, and dynamically provide collections of tools to your ADK agents, leading to more modular, maintainable, and adaptable agentic applications.



Authenticating with Tools¶
python_only

Core Concepts¶
Many tools need to access protected resources (like user data in Google Calendar, Salesforce records, etc.) and require authentication. ADK provides a system to handle various authentication methods securely.

The key components involved are:

AuthScheme: Defines how an API expects authentication credentials (e.g., as an API Key in a header, an OAuth 2.0 Bearer token). ADK supports the same types of authentication schemes as OpenAPI 3.0. To know more about what each type of credential is, refer to OpenAPI doc: Authentication. ADK uses specific classes like APIKey, HTTPBearer, OAuth2, OpenIdConnectWithConfig.
AuthCredential: Holds the initial information needed to start the authentication process (e.g., your application's OAuth Client ID/Secret, an API key value). It includes an auth_type (like API_KEY, OAUTH2, SERVICE_ACCOUNT) specifying the credential type.
The general flow involves providing these details when configuring a tool. ADK then attempts to automatically exchange the initial credential for a usable one (like an access token) before the tool makes an API call. For flows requiring user interaction (like OAuth consent), a specific interactive process involving the Agent Client application is triggered.

Supported Initial Credential Types¶
API_KEY: For simple key/value authentication. Usually requires no exchange.
HTTP: Can represent Basic Auth (not recommended/supported for exchange) or already obtained Bearer tokens. If it's a Bearer token, no exchange is needed.
OAUTH2: For standard OAuth 2.0 flows. Requires configuration (client ID, secret, scopes) and often triggers the interactive flow for user consent.
OPEN_ID_CONNECT: For authentication based on OpenID Connect. Similar to OAuth2, often requires configuration and user interaction.
SERVICE_ACCOUNT: For Google Cloud Service Account credentials (JSON key or Application Default Credentials). Typically exchanged for a Bearer token.
Configuring Authentication on Tools¶
You set up authentication when defining your tool:

RestApiTool / OpenAPIToolset: Pass auth_scheme and auth_credential during initialization

GoogleApiToolSet Tools: ADK has built-in 1st party tools like Google Calendar, BigQuery etc,. Use the toolset's specific method.

APIHubToolset / ApplicationIntegrationToolset: Pass auth_scheme and auth_credentialduring initialization, if the API managed in API Hub / provided by Application Integration requires authentication.

WARNING

Storing sensitive credentials like access tokens and especially refresh tokens directly in the session state might pose security risks depending on your session storage backend (SessionService) and overall application security posture.

InMemorySessionService: Suitable for testing and development, but data is lost when the process ends. Less risk as it's transient.
Database/Persistent Storage: Strongly consider encrypting the token data before storing it in the database using a robust encryption library (like cryptography) and managing encryption keys securely (e.g., using a key management service).
Secure Secret Stores: For production environments, storing sensitive credentials in a dedicated secret manager (like Google Cloud Secret Manager or HashiCorp Vault) is the most recommended approach. Your tool could potentially store only short-lived access tokens or secure references (not the refresh token itself) in the session state, fetching the necessary secrets from the secure store when needed.
Journey 1: Building Agentic Applications with Authenticated Tools¶
This section focuses on using pre-existing tools (like those from RestApiTool/ OpenAPIToolset, APIHubToolset, GoogleApiToolSet) that require authentication within your agentic application. Your main responsibility is configuring the tools and handling the client-side part of interactive authentication flows (if required by the tool).

1. Configuring Tools with Authentication¶
When adding an authenticated tool to your agent, you need to provide its required AuthScheme and your application's initial AuthCredential.

A. Using OpenAPI-based Toolsets (OpenAPIToolset, APIHubToolset, etc.)

Pass the scheme and credential during toolset initialization. The toolset applies them to all generated tools. Here are few ways to create tools with authentication in ADK.


API Key
OAuth2
Service Account
OpenID connect
Create a tool requiring an API Key.


from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential
from google.adk.tools.apihub_tool.apihub_toolset import APIHubToolset
auth_scheme, auth_credential = token_to_scheme_credential(
   "apikey", "query", "apikey", YOUR_API_KEY_STRING
)
sample_api_toolset = APIHubToolset(
   name="sample-api-requiring-api-key",
   description="A tool using an API protected by API Key",
   apihub_resource_name="...",
   auth_scheme=auth_scheme,
   auth_credential=auth_credential,
)

B. Using Google API Toolsets (e.g., calendar_tool_set)

These toolsets often have dedicated configuration methods.

Tip: For how to create a Google OAuth Client ID & Secret, see this guide: Get your Google API Client ID


# Example: Configuring Google Calendar Tools
from google.adk.tools.google_api_tool import calendar_tool_set

client_id = "YOUR_GOOGLE_OAUTH_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_GOOGLE_OAUTH_CLIENT_SECRET"

# Use the specific configure method for this toolset type
calendar_tool_set.configure_auth(
    client_id=oauth_client_id, client_secret=oauth_client_secret
)

# agent = LlmAgent(..., tools=calendar_tool_set.get_tool('calendar_tool_set'))
The sequence diagram of auth request flow (where tools are requesting auth credentials) looks like below:

Authentication

2. Handling the Interactive OAuth/OIDC Flow (Client-Side)¶
If a tool requires user login/consent (typically OAuth 2.0 or OIDC), the ADK framework pauses execution and signals your Agent Client application. There are two cases:

Agent Client application runs the agent directly (via runner.run_async) in the same process. e.g. UI backend, CLI app, or Spark job etc.
Agent Client application interacts with ADK's fastapi server via /run or /run_sse endpoint. While ADK's fastapi server could be setup on the same server or different server as Agent Client application
The second case is a special case of first case, because /run or /run_sse endpoint also invokes runner.run_async. The only differences are:

Whether to call a python function to run the agent (first case) or call a service endpoint to run the agent (second case).
Whether the result events are in-memory objects (first case) or serialized json string in http response (second case).
Below sections focus on the first case and you should be able to map it to the second case very straightforward. We will also describe some differences to handle for the second case if necessary.

Here's the step-by-step process for your client application:

Step 1: Run Agent & Detect Auth Request

Initiate the agent interaction using runner.run_async.
Iterate through the yielded events.
Look for a specific function call event whose function call has a special name: adk_request_credential. This event signals that user interaction is needed. You can use helper functions to identify this event and extract necessary information. (For the second case, the logic is similar. You deserialize the event from the http response).

# runner = Runner(...)
# session = await session_service.create_session(...)
# content = types.Content(...) # User's initial query

print("\nRunning agent...")
events_async = runner.run_async(
    session_id=session.id, user_id='user', new_message=content
)

auth_request_function_call_id, auth_config = None, None

async for event in events_async:
    # Use helper to check for the specific auth request event
    if (auth_request_function_call := get_auth_request_function_call(event)):
        print("--> Authentication required by agent.")
        # Store the ID needed to respond later
        if not (auth_request_function_call_id := auth_request_function_call.id):
            raise ValueError(f'Cannot get function call id from function call: {auth_request_function_call}')
        # Get the AuthConfig containing the auth_uri etc.
        auth_config = get_auth_config(auth_request_function_call)
        break # Stop processing events for now, need user interaction

if not auth_request_function_call_id:
    print("\nAuth not required or agent finished.")
    # return # Or handle final response if received
Helper functions helpers.py:


from google.adk.events import Event
from google.adk.auth import AuthConfig # Import necessary type
from google.genai import types

def get_auth_request_function_call(event: Event) -> types.FunctionCall:
    # Get the special auth request function call from the event
    if not event.content or event.content.parts:
        return
    for part in event.content.parts:
        if (
            part 
            and part.function_call 
            and part.function_call.name == 'adk_request_credential'
            and event.long_running_tool_ids 
            and part.function_call.id in event.long_running_tool_ids
        ):

            return part.function_call

def get_auth_config(auth_request_function_call: types.FunctionCall) -> AuthConfig:
    # Extracts the AuthConfig object from the arguments of the auth request function call
    if not auth_request_function_call.args or not (auth_config := auth_request_function_call.args.get('auth_config')):
        raise ValueError(f'Cannot get auth config from function call: {auth_request_function_call}')
    if not isinstance(auth_config, AuthConfig):
        raise ValueError(f'Cannot get auth config {auth_config} is not an instance of AuthConfig.')
    return auth_config
Step 2: Redirect User for Authorization

Get the authorization URL (auth_uri) from the auth_config extracted in the previous step.
Crucially, append your application's redirect_uri as a query parameter to this auth_uri. This redirect_uri must be pre-registered with your OAuth provider (e.g., Google Cloud Console, Okta admin panel).
Direct the user to this complete URL (e.g., open it in their browser).

# (Continuing after detecting auth needed)

if auth_request_function_call_id and auth_config:
    # Get the base authorization URL from the AuthConfig
    base_auth_uri = auth_config.exchanged_auth_credential.oauth2.auth_uri

    if base_auth_uri:
        redirect_uri = 'http://localhost:8000/callback' # MUST match your OAuth client app config
        # Append redirect_uri (use urlencode in production)
        auth_request_uri = base_auth_uri + f'&redirect_uri={redirect_uri}'
        # Now you need to redirect your end user to this auth_request_uri or ask them to open this auth_request_uri in their browser
        # This auth_request_uri should be served by the corresponding auth provider and the end user should login and authorize your applicaiton to access their data
        # And then the auth provider will redirect the end user to the redirect_uri you provided
        # Next step: Get this callback URL from the user (or your web server handler)
    else:
         print("ERROR: Auth URI not found in auth_config.")
         # Handle error
Step 3. Handle the Redirect Callback (Client):

Your application must have a mechanism (e.g., a web server route at the redirect_uri) to receive the user after they authorize the application with the provider.
The provider redirects the user to your redirect_uri and appends an authorization_code (and potentially state, scope) as query parameters to the URL.
Capture the full callback URL from this incoming request.
(This step happens outside the main agent execution loop, in your web server or equivalent callback handler.)
Step 4. Send Authentication Result Back to ADK (Client):

Once you have the full callback URL (containing the authorization code), retrieve the auth_request_function_call_id and the auth_config object saved in Client Step 1.
Set the captured callback URL into the exchanged_auth_credential.oauth2.auth_response_uri field. Also ensure exchanged_auth_credential.oauth2.redirect_uri contains the redirect URI you used.
Create a types.Content object containing a types.Part with a types.FunctionResponse.
Set name to "adk_request_credential". (Note: This is a special name for ADK to proceed with authentication. Do not use other names.)
Set id to the auth_request_function_call_id you saved.
Set response to the serialized (e.g., .model_dump()) updated AuthConfig object.
Call runner.run_async again for the same session, passing this FunctionResponse content as the new_message.

# (Continuing after user interaction)

    # Simulate getting the callback URL (e.g., from user paste or web handler)
    auth_response_uri = await get_user_input(
        f'Paste the full callback URL here:\n> '
    )
    auth_response_uri = auth_response_uri.strip() # Clean input

    if not auth_response_uri:
        print("Callback URL not provided. Aborting.")
        return

    # Update the received AuthConfig with the callback details
    auth_config.exchanged_auth_credential.oauth2.auth_response_uri = auth_response_uri
    # Also include the redirect_uri used, as the token exchange might need it
    auth_config.exchanged_auth_credential.oauth2.redirect_uri = redirect_uri

    # Construct the FunctionResponse Content object
    auth_content = types.Content(
        role='user', # Role can be 'user' when sending a FunctionResponse
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=auth_request_function_call_id,       # Link to the original request
                    name='adk_request_credential', # Special framework function name
                    response=auth_config.model_dump() # Send back the *updated* AuthConfig
                )
            )
        ],
    )

    # --- Resume Execution ---
    print("\nSubmitting authentication details back to the agent...")
    events_async_after_auth = runner.run_async(
        session_id=session.id,
        user_id='user',
        new_message=auth_content, # Send the FunctionResponse back
    )

    # --- Process Final Agent Output ---
    print("\n--- Agent Response after Authentication ---")
    async for event in events_async_after_auth:
        # Process events normally, expecting the tool call to succeed now
        print(event) # Print the full event for inspection
Step 5: ADK Handles Token Exchange & Tool Retry and gets Tool result

ADK receives the FunctionResponse for adk_request_credential.
It uses the information in the updated AuthConfig (including the callback URL containing the code) to perform the OAuth token exchange with the provider's token endpoint, obtaining the access token (and possibly refresh token).
ADK internally makes these tokens available by setting them in the session state).
ADK automatically retries the original tool call (the one that initially failed due to missing auth).
This time, the tool finds the valid tokens (via tool_context.get_auth_response()) and successfully executes the authenticated API call.
The agent receives the actual result from the tool and generates its final response to the user.
The sequence diagram of auth response flow (where Agent Client send back the auth response and ADK retries tool calling) looks like below:

Authentication

Journey 2: Building Custom Tools (FunctionTool) Requiring Authentication¶
This section focuses on implementing the authentication logic inside your custom Python function when creating a new ADK Tool. We will implement a FunctionTool as an example.

Prerequisites¶
Your function signature must include tool_context: ToolContext. ADK automatically injects this object, providing access to state and auth mechanisms.


from google.adk.tools import FunctionTool, ToolContext
from typing import Dict

def my_authenticated_tool_function(param1: str, ..., tool_context: ToolContext) -> dict:
    # ... your logic ...
    pass

my_tool = FunctionTool(func=my_authenticated_tool_function)
Authentication Logic within the Tool Function¶
Implement the following steps inside your function:

Step 1: Check for Cached & Valid Credentials:

Inside your tool function, first check if valid credentials (e.g., access/refresh tokens) are already stored from a previous run in this session. Credentials for the current sessions should be stored in tool_context.invocation_context.session.state (a dictionary of state) Check existence of existing credentials by checking tool_context.invocation_context.session.state.get(credential_name, None).


from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Inside your tool function
TOKEN_CACHE_KEY = "my_tool_tokens" # Choose a unique key
SCOPES = ["scope1", "scope2"] # Define required scopes

creds = None
cached_token_info = tool_context.state.get(TOKEN_CACHE_KEY)
if cached_token_info:
    try:
        creds = Credentials.from_authorized_user_info(cached_token_info, SCOPES)
        if not creds.valid and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            tool_context.state[TOKEN_CACHE_KEY] = json.loads(creds.to_json()) # Update cache
        elif not creds.valid:
            creds = None # Invalid, needs re-auth
            tool_context.state[TOKEN_CACHE_KEY] = None
    except Exception as e:
        print(f"Error loading/refreshing cached creds: {e}")
        creds = None
        tool_context.state[TOKEN_CACHE_KEY] = None

if creds and creds.valid:
    # Skip to Step 5: Make Authenticated API Call
    pass
else:
    # Proceed to Step 2...
    pass
Step 2: Check for Auth Response from Client

If Step 1 didn't yield valid credentials, check if the client just completed the interactive flow by calling exchanged_credential = tool_context.get_auth_response().
This returns the updated exchanged_credential object sent back by the client (containing the callback URL in auth_response_uri).

# Use auth_scheme and auth_credential configured in the tool.
# exchanged_credential: AuthCredential | None

exchanged_credential = tool_context.get_auth_response(AuthConfig(
  auth_scheme=auth_scheme,
  raw_auth_credential=auth_credential,
))
# If exchanged_credential is not None, then there is already an exchanged credetial from the auth response. 
if exchanged_credential:
   # ADK exchanged the access token already for us
        access_token = exchanged_credential.oauth2.access_token
        refresh_token = exchanged_credential.oauth2.refresh_token
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=auth_scheme.flows.authorizationCode.tokenUrl,
            client_id=auth_credential.oauth2.client_id,
            client_secret=auth_credential.oauth2.client_secret,
            scopes=list(auth_scheme.flows.authorizationCode.scopes.keys()),
        )
    # Cache the token in session state and call the API, skip to step 5
Step 3: Initiate Authentication Request

If no valid credentials (Step 1.) and no auth response (Step 2.) are found, the tool needs to start the OAuth flow. Define the AuthScheme and initial AuthCredential and call tool_context.request_credential(). Return a response indicating authorization is needed.


# Use auth_scheme and auth_credential configured in the tool.

  tool_context.request_credential(AuthConfig(
    auth_scheme=auth_scheme,
    raw_auth_credential=auth_credential,
  ))
  return {'pending': true, 'message': 'Awaiting user authentication.'}

# By setting request_credential, ADK detects a pending authentication event. It pauses execution and ask end user to login.
Step 4: Exchange Authorization Code for Tokens

ADK automatically generates oauth authorization URL and presents it to your Agent Client application. your Agent Client application should follow the same way described in Journey 1 to redirect the user to the authorization URL (with redirect_uri appended). Once a user completes the login flow following the authorization URL and ADK extracts the authentication callback url from Agent Client applications, automatically parses the auth code, and generates auth token. At the next Tool call, tool_context.get_auth_response in step 2 will contain a valid credential to use in subsequent API calls.

Step 5: Cache Obtained Credentials

After successfully obtaining the token from ADK (Step 2) or if the token is still valid (Step 1), immediately store the new Credentials object in tool_context.state (serialized, e.g., as JSON) using your cache key.


# Inside your tool function, after obtaining 'creds' (either refreshed or newly exchanged)
# Cache the new/refreshed tokens
tool_context.state[TOKEN_CACHE_KEY] = json.loads(creds.to_json())
print(f"DEBUG: Cached/updated tokens under key: {TOKEN_CACHE_KEY}")
# Proceed to Step 6 (Make API Call)
Step 6: Make Authenticated API Call

Once you have a valid Credentials object (creds from Step 1 or Step 4), use it to make the actual call to the protected API using the appropriate client library (e.g., googleapiclient, requests). Pass the credentials=creds argument.
Include error handling, especially for HttpError 401/403, which might mean the token expired or was revoked between calls. If you get such an error, consider clearing the cached token (tool_context.state.pop(...)) and potentially returning the auth_required status again to force re-authentication.

# Inside your tool function, using the valid 'creds' object
# Ensure creds is valid before proceeding
if not creds or not creds.valid:
   return {"status": "error", "error_message": "Cannot proceed without valid credentials."}

try:
   service = build("calendar", "v3", credentials=creds) # Example
   api_result = service.events().list(...).execute()
   # Proceed to Step 7
except Exception as e:
   # Handle API errors (e.g., check for 401/403, maybe clear cache and re-request auth)
   print(f"ERROR: API call failed: {e}")
   return {"status": "error", "error_message": f"API call failed: {e}"}
Step 7: Return Tool Result

After a successful API call, process the result into a dictionary format that is useful for the LLM.
Crucially, include a along with the data.

# Inside your tool function, after successful API call
    processed_result = [...] # Process api_result for the LLM
    return {"status": "success", "data": processed_result}
Full Code

Tools and Agent
Agent CLI
Helper
Spec
tools_and_agent.py

import os

from google.adk.auth.auth_schemes import OpenIdConnectWithConfig
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset
from google.adk.agents.llm_agent import LlmAgent

# --- Authentication Configuration ---
# This section configures how the agent will handle authentication using OpenID Connect (OIDC),
# often layered on top of OAuth 2.0.

# Define the Authentication Scheme using OpenID Connect.
# This object tells the ADK *how* to perform the OIDC/OAuth2 flow.
# It requires details specific to your Identity Provider (IDP), like Google OAuth, Okta, Auth0, etc.
# Note: Replace the example Okta URLs and credentials with your actual IDP details.
# All following fields are required, and available from your IDP.
auth_scheme = OpenIdConnectWithConfig(
    # The URL of the IDP's authorization endpoint where the user is redirected to log in.
    authorization_endpoint="https://your-endpoint.okta.com/oauth2/v1/authorize",
    # The URL of the IDP's token endpoint where the authorization code is exchanged for tokens.
    token_endpoint="https://your-token-endpoint.okta.com/oauth2/v1/token",
    # The scopes (permissions) your application requests from the IDP.
    # 'openid' is standard for OIDC. 'profile' and 'email' request user profile info.
    scopes=['openid', 'profile', "email"]
)

# Define the Authentication Credentials for your specific application.
# This object holds the client identifier and secret that your application uses
# to identify itself to the IDP during the OAuth2 flow.
# !! SECURITY WARNING: Avoid hardcoding secrets in production code. !!
# !! Use environment variables or a secret management system instead. !!
auth_credential = AuthCredential(
  auth_type=AuthCredentialTypes.OPEN_ID_CONNECT,
  oauth2=OAuth2Auth(
    client_id="CLIENT_ID",
    client_secret="CIENT_SECRET",
  )
)


# --- Toolset Configuration from OpenAPI Specification ---
# This section defines a sample set of tools the agent can use, configured with Authentication
# from steps above.
# This sample set of tools use endpoints protected by Okta and requires an OpenID Connect flow
# to acquire end user credentials.
with open(os.path.join(os.path.dirname(__file__), 'spec.yaml'), 'r') as f:
    spec_content = f.read()

userinfo_toolset = OpenAPIToolset(
   spec_str=spec_content,
   spec_str_type='yaml',
   # ** Crucially, associate the authentication scheme and credentials with these tools. **
   # This tells the ADK that the tools require the defined OIDC/OAuth2 flow.
   auth_scheme=auth_scheme,
   auth_credential=auth_credential,
)

# --- Agent Configuration ---
# Configure and create the main LLM Agent.
root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='enterprise_assistant',
    instruction='Help user integrate with multiple enterprise systems, including retrieving user information which may require authentication.',
    tools=userinfo_toolset.get_tools(),
)

# --- Ready for Use ---
# The `root_agent` is now configured with tools protected by OIDC/OAuth2 authentication.
# When the agent attempts to use one of these tools, the ADK framework will automatically
# trigger the authentication flow defined by `auth_scheme` and `auth_credential`
# if valid credentials are not already available in the session.
# The subsequent interaction flow would guide the user through the login process and handle
# token exchanging, and automatically attach the exchanged token to the endpoint defined in
# the tool.



# OpenAPI Integration¶
python_only

Integrating REST APIs with OpenAPI¶
ADK simplifies interacting with external REST APIs by automatically generating callable tools directly from an OpenAPI Specification (v3.x). This eliminates the need to manually define individual function tools for each API endpoint.

Core Benefit

Use OpenAPIToolset to instantly create agent tools (RestApiTool) from your existing API documentation (OpenAPI spec), enabling agents to seamlessly call your web services.

Key Components¶
OpenAPIToolset: This is the primary class you'll use. You initialize it with your OpenAPI specification, and it handles the parsing and generation of tools.
RestApiTool: This class represents a single, callable API operation (like GET /pets/{petId} or POST /pets). OpenAPIToolset creates one RestApiTool instance for each operation defined in your spec.
How it Works¶
The process involves these main steps when you use OpenAPIToolset:

Initialization & Parsing:

You provide the OpenAPI specification to OpenAPIToolset either as a Python dictionary, a JSON string, or a YAML string.
The toolset internally parses the spec, resolving any internal references ($ref) to understand the complete API structure.
Operation Discovery:

It identifies all valid API operations (e.g., GET, POST, PUT, DELETE) defined within the paths object of your specification.
Tool Generation:

For each discovered operation, OpenAPIToolset automatically creates a corresponding RestApiTool instance.
Tool Name: Derived from the operationId in the spec (converted to snake_case, max 60 chars). If operationId is missing, a name is generated from the method and path.
Tool Description: Uses the summary or description from the operation for the LLM.
API Details: Stores the required HTTP method, path, server base URL, parameters (path, query, header, cookie), and request body schema internally.
RestApiTool Functionality: Each generated RestApiTool:

Schema Generation: Dynamically creates a FunctionDeclaration based on the operation's parameters and request body. This schema tells the LLM how to call the tool (what arguments are expected).
Execution: When called by the LLM, it constructs the correct HTTP request (URL, headers, query params, body) using the arguments provided by the LLM and the details from the OpenAPI spec. It handles authentication (if configured) and executes the API call using the requests library.
Response Handling: Returns the API response (typically JSON) back to the agent flow.
Authentication: You can configure global authentication (like API keys or OAuth - see Authentication for details) when initializing OpenAPIToolset. This authentication configuration is automatically applied to all generated RestApiTool instances.

Usage Workflow¶
Follow these steps to integrate an OpenAPI spec into your agent:

Obtain Spec: Get your OpenAPI specification document (e.g., load from a .json or .yaml file, fetch from a URL).
Instantiate Toolset: Create an OpenAPIToolset instance, passing the spec content and type (spec_str/spec_dict, spec_str_type). Provide authentication details (auth_scheme, auth_credential) if required by the API.


from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset

# Example with a JSON string
openapi_spec_json = '...' # Your OpenAPI JSON string
toolset = OpenAPIToolset(spec_str=openapi_spec_json, spec_str_type="json")

# Example with a dictionary
# openapi_spec_dict = {...} # Your OpenAPI spec as a dict
# toolset = OpenAPIToolset(spec_dict=openapi_spec_dict)
Add to Agent: Include the retrieved tools in your LlmAgent's tools list.


from google.adk.agents import LlmAgent

my_agent = LlmAgent(
    name="api_interacting_agent",
    model="gemini-2.0-flash", # Or your preferred model
    tools=[toolset], # Pass the toolset
    # ... other agent config ...
)
Instruct Agent: Update your agent's instructions to inform it about the new API capabilities and the names of the tools it can use (e.g., list_pets, create_pet). The tool descriptions generated from the spec will also help the LLM.

Run Agent: Execute your agent using the Runner. When the LLM determines it needs to call one of the APIs, it will generate a function call targeting the appropriate RestApiTool, which will then handle the HTTP request automatically.
Example¶
This example demonstrates generating tools from a simple Pet Store OpenAPI spec (using httpbin.org for mock responses) and interacting with them via an agent.

Code: Pet Store API
openapi_example.py

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import uuid # For unique session IDs
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# --- OpenAPI Tool Imports ---
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset

# --- Load Environment Variables (If ADK tools need them, e.g., API keys) ---
load_dotenv() # Create a .env file in the same directory if needed

# --- Constants ---
APP_NAME_OPENAPI = "openapi_petstore_app"
USER_ID_OPENAPI = "user_openapi_1"
SESSION_ID_OPENAPI = f"session_openapi_{uuid.uuid4()}" # Unique session ID
AGENT_NAME_OPENAPI = "petstore_manager_agent"
GEMINI_MODEL = "gemini-2.0-flash"

# --- Sample OpenAPI Specification (JSON String) ---
# A basic Pet Store API example using httpbin.org as a mock server
openapi_spec_string = """
{
  "openapi": "3.0.0",
  "info": {
    "title": "Simple Pet Store API (Mock)",
    "version": "1.0.1",
    "description": "An API to manage pets in a store, using httpbin for responses."
  },
  "servers": [
    {
      "url": "https://httpbin.org",
      "description": "Mock server (httpbin.org)"
    }
  ],
  "paths": {
    "/get": {
      "get": {
        "summary": "List all pets (Simulated)",
        "operationId": "listPets",
        "description": "Simulates returning a list of pets. Uses httpbin's /get endpoint which echoes query parameters.",
        "parameters": [
          {
            "name": "limit",
            "in": "query",
            "description": "Maximum number of pets to return",
            "required": false,
            "schema": { "type": "integer", "format": "int32" }
          },
          {
             "name": "status",
             "in": "query",
             "description": "Filter pets by status",
             "required": false,
             "schema": { "type": "string", "enum": ["available", "pending", "sold"] }
          }
        ],
        "responses": {
          "200": {
            "description": "A list of pets (echoed query params).",
            "content": { "application/json": { "schema": { "type": "object" } } }
          }
        }
      }
    },
    "/post": {
      "post": {
        "summary": "Create a pet (Simulated)",
        "operationId": "createPet",
        "description": "Simulates adding a new pet. Uses httpbin's /post endpoint which echoes the request body.",
        "requestBody": {
          "description": "Pet object to add",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["name"],
                "properties": {
                  "name": {"type": "string", "description": "Name of the pet"},
                  "tag": {"type": "string", "description": "Optional tag for the pet"}
                }
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "Pet created successfully (echoed request body).",
            "content": { "application/json": { "schema": { "type": "object" } } }
          }
        }
      }
    },
    "/get?petId={petId}": {
      "get": {
        "summary": "Info for a specific pet (Simulated)",
        "operationId": "showPetById",
        "description": "Simulates returning info for a pet ID. Uses httpbin's /get endpoint.",
        "parameters": [
          {
            "name": "petId",
            "in": "path",
            "description": "This is actually passed as a query param to httpbin /get",
            "required": true,
            "schema": { "type": "integer", "format": "int64" }
          }
        ],
        "responses": {
          "200": {
            "description": "Information about the pet (echoed query params)",
            "content": { "application/json": { "schema": { "type": "object" } } }
          },
          "404": { "description": "Pet not found (simulated)" }
        }
      }
    }
  }
}
"""

# --- Create OpenAPIToolset ---
petstore_toolset = OpenAPIToolset(
    spec_str=openapi_spec_string,
    spec_str_type='json',
    # No authentication needed for httpbin.org
)

# --- Agent Definition ---
root_agent = LlmAgent(
    name=AGENT_NAME_OPENAPI,
    model=GEMINI_MODEL,
    tools=[petstore_toolset], # Pass the list of RestApiTool objects
    instruction="""You are a Pet Store assistant managing pets via an API.
    Use the available tools to fulfill user requests.
    When creating a pet, confirm the details echoed back by the API.
    When listing pets, mention any filters used (like limit or status).
    When showing a pet by ID, state the ID you requested.
    """,
    description="Manages a Pet Store using tools generated from an OpenAPI spec."
)

# --- Session and Runner Setup ---
async def setup_session_and_runner():
    session_service_openapi = InMemorySessionService()
    runner_openapi = Runner(
        agent=root_agent,
        app_name=APP_NAME_OPENAPI,
        session_service=session_service_openapi,
    )
    await session_service_openapi.create_session(
        app_name=APP_NAME_OPENAPI,
        user_id=USER_ID_OPENAPI,
        session_id=SESSION_ID_OPENAPI,
    )
    return runner_openapi

# --- Agent Interaction Function ---
async def call_openapi_agent_async(query, runner_openapi):
    print("\n--- Running OpenAPI Pet Store Agent ---")
    print(f"Query: {query}")

    content = types.Content(role='user', parts=[types.Part(text=query)])
    final_response_text = "Agent did not provide a final text response."
    try:
        async for event in runner_openapi.run_async(
            user_id=USER_ID_OPENAPI, session_id=SESSION_ID_OPENAPI, new_message=content
            ):
            # Optional: Detailed event logging for debugging
            # print(f"  DEBUG Event: Author={event.author}, Type={'Final' if event.is_final_response() else 'Intermediate'}, Content={str(event.content)[:100]}...")
            if event.get_function_calls():
                call = event.get_function_calls()[0]
                print(f"  Agent Action: Called function '{call.name}' with args {call.args}")
            elif event.get_function_responses():
                response = event.get_function_responses()[0]
                print(f"  Agent Action: Received response for '{response.name}'")
                # print(f"  Tool Response Snippet: {str(response.response)[:200]}...") # Uncomment for response details
            elif event.is_final_response() and event.content and event.content.parts:
                # Capture the last final text response
                final_response_text = event.content.parts[0].text.strip()

        print(f"Agent Final Response: {final_response_text}")

    except Exception as e:
        print(f"An error occurred during agent run: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for errors
    print("-" * 30)

# --- Run Examples ---
async def run_openapi_example():
    runner_openapi = await setup_session_and_runner()

    # Trigger listPets
    await call_openapi_agent_async("Show me the pets available.", runner_openapi)
    # Trigger createPet
    await call_openapi_agent_async("Please add a new dog named 'Dukey'.", runner_openapi)
    # Trigger showPetById
    await call_openapi_agent_async("Get info for pet with ID 123.", runner_openapi)

# --- Execute ---
if __name__ == "__main__":
    print("Executing OpenAPI example...")
    # Use asyncio.run() for top-level execution
    try:
        asyncio.run(run_openapi_example())
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            print("Info: Cannot run asyncio.run from a running event loop (e.g., Jupyter/Colab).")
            # If in Jupyter/Colab, you might need to run like this:
            # await run_openapi_example()
        else:
            raise e
    print("OpenAPI example finished.")