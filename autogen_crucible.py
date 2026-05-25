import autogen

# 1. Point AutoGen to your local Ollama
config_list = [
    {
        "model": "qwen3:8b",
        "base_url": "http://localhost:11434/v1", # Ollama OpenAI-compatible endpoint
        "api_key": "ollama", # Dummy key, Ollama ignores it
        "price": [0, 0], # Tells AutoGen this is free
    }
]

llm_config = {
    "config_list": config_list,
    "temperature": 0.7,
    "timeout": 120,
}

# 2. Define your agents - matches your claude-flow roles
coordinator = autogen.UserProxyAgent(
    name="Coordinator",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={"work_dir": "crucible_workspace", "use_docker": False},
    system_message="You coordinate the workflow and run code when needed."
)

architect = autogen.AssistantAgent(
    name="Architect",
    llm_config=llm_config,
    system_message="You design system architecture. Output clear technical specs and file structures."
)

coder_1 = autogen.AssistantAgent(
    name="Coder_1",
    llm_config=llm_config,
    system_message="You implement features in Python/TypeScript. Write clean, tested code."
)

coder_2 = autogen.AssistantAgent(
    name="Coder_2",
    llm_config=llm_config,
    system_message="You implement features in Python/TypeScript. Write clean, tested code."
)

tester = autogen.AssistantAgent(
    name="Tester",
    llm_config=llm_config,
    system_message="You write unit tests and do QA. Find bugs and edge cases."
)

reviewer = autogen.AssistantAgent(
    name="Reviewer",
    llm_config=llm_config,
    system_message="You review code for quality, security, and best practices. Approve or request changes."
)

# 3. Create the group chat = your swarm
groupchat = autogen.GroupChat(
    agents=[coordinator, architect, coder_1, coder_2, tester, reviewer],
    messages=[],
    max_round=20, # Limits total back-and-forth
    speaker_selection_method="auto" # LLM picks who talks next
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config
)

# 4. Kick off the task
coordinator.initiate_chat(
    manager,
    message="We need to build out the crucible. Architect, start with system design. Team, let's ship a working MVP with core features, tests, and code review."
)