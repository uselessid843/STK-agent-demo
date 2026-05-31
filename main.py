from agent import create_agent
from dotenv import load_dotenv

load_dotenv()

def run():
    """Simple chat loop to interact with the agent."""
    print("\n🏗️  Construction Daily Report Agent")
    print("Type 'quit' to exit.\n")

    agent = create_agent()

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Exiting.")
            break

        print("\nAgent thinking...\n")

        result = agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })

        # LangGraph returns messages list — get the last one
        response = result["messages"][-1].content
        print(f"Agent: {response}\n")

if __name__ == "__main__":
    run()