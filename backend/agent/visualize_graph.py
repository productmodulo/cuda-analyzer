from agent.graph import create_agent_graph
import os

def generate_graph_viz(output_path: str = "agent_workflow.png"):
    app = create_agent_graph()
    try:
        # Generate Mermaid PNG
        png_data = app.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(png_data)
        print(f"Successfully generated graph visualization at: {output_path}")
    except Exception as e:
        print(f"Failed to generate graph visualization: {e}")
        print("Note: This requires 'pyppeteer' or 'graphviz' dependencies for draw_mermaid_png().")

if __name__ == "__main__":
    generate_graph_viz()
