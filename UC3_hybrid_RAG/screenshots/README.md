Screenshots

Capture only the screenshots listed below for the assessment submission. The goal is to show the working application, the retrieval evidence, the graph view, and the unsupported query behavior without adding extra images.

answer_example.png

Show the Streamlit app after asking a supported question such as "What is Coulombs Law?"

The screenshot should include the question, the generated answer, and the citation area. This is useful because it shows the normal user facing flow and proves that the answer is tied to the source document.

retrieval_evidence.png

Show the retrieval evidence section for the same or another supported question.

The screenshot should include semantic chunks, keyword chunks, or the debug panel with retrieved chunks. This helps the reviewer see that the answer was built from visible source evidence rather than only from the model response.

graph_view.png

Show the graph retrieval output in the Streamlit "Graph nodes" tab or the related Neo4j browser view.

The screenshot should include concept or formula nodes connected to the question topic. This is useful because Neo4j is one of the required retrieval paths in the Hybrid RAG design.

unsupported_query.png

Ask a question that is outside the Physics PDF.

The screenshot should show the fixed response: Information not found in the source document. This demonstrates the grounding rule and confirms that unsupported questions are refused instead of answered from general model knowledge.
