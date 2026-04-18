import asyncio
from agent.graph import create_agent_graph
from agent.state import AgentState, AgentStatus

async def invoke_agent(cuda_code: str, question: str, max_iterations: int = 3):
    app = create_agent_graph()
    
    # Initial state
    initial_state = AgentState(
        original_code=cuda_code,
        user_question=question,
        iteration_count=0,
        max_iterations=max_iterations,
        status=AgentStatus.START
    )
    
    # Run the graph
    final_state = await app.ainvoke(initial_state)
    
    return final_state
