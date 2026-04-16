import os
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from core.ingestor import CHROMA_PERSIST_DIR, DocumentIngestor

# System Prompts
LEGAL_SYSTEM_PROMPT = """You are a strictly professional Legal AI Advisor named LexiGuard AI. 
Your role is to identify legal risks, summarize clauses, and provide legal insights based on the provided documents.
You must maintain a formal, objective, and precise tone.
Always refer to the provided context. If the answer is not in the context, state that clearly.
Always cite the specific page number and document name when referencing parts of the document.
"""

DISCLAIMER = "\n\n**Disclaimer:** *The insights provided by LexiGuard AI are generated for informational purposes only and do not constitute formal legal advice. Please consult with a qualified attorney before taking any legal action.*"

class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    context_docs: List[Any]
    analysis: str
    verified_response: str

class LegalAgent:
    def __init__(self):
        llm_endpoint = HuggingFaceEndpoint(
            repo_id="Qwen/Qwen2.5-72B-Instruct",
            task="text-generation",
            max_new_tokens=512,
            do_sample=False,
            temperature=0.1
        )
        self.llm = ChatHuggingFace(llm=llm_endpoint)
        # Initialize chroma store
        try:
            self.vectorstore = Chroma(
                persist_directory=CHROMA_PERSIST_DIR,
                embedding_function=DocumentIngestor().embeddings
            )
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        except Exception:
            self.retriever = None # Will handle dynamically or alert if no data

        # Build Grapph
        builder = StateGraph(GraphState)
        builder.add_node("search", self.search_node)
        builder.add_node("analyze", self.analyze_node)
        builder.add_node("verify", self.verify_node)
        builder.add_node("respond", self.respond_node)

        # Define edges
        builder.add_edge(START, "search")
        builder.add_edge("search", "analyze")
        builder.add_edge("analyze", "verify")
        builder.add_edge("verify", "respond")
        builder.add_edge("respond", END)

        self.graph = builder.compile()

    def search_node(self, state: GraphState) -> Dict:
        """Retrieve relevant context for the latest user query."""
        if not self.retriever:
            return {"context_docs": []}

        # Get the latest message
        latest_msg = state["messages"][-1].content
        docs = self.retriever.invoke(latest_msg)
        return {"context_docs": docs}

    def analyze_node(self, state: GraphState) -> Dict:
        """Analyze the user's request against the retrieved context."""
        latest_msg = state["messages"][-1].content
        context_str = "\\n\\n".join(
            [f"Source: {doc.metadata.get('document_name', 'Unknown')} (Page {doc.metadata.get('page', 'Unknown')})\\n{doc.page_content}" 
             for doc in state["context_docs"]]
        )

        prompt = f"""Using the following document context, provide a preliminary legal analysis for the user's query. Identify any major clauses or risks.

Context:
{context_str}

User Query: {latest_msg}

Preliminary Analysis:"""
        
        response = self.llm.invoke([SystemMessage(content=LEGAL_SYSTEM_PROMPT), HumanMessage(content=prompt)])
        return {"analysis": response.content}

    def verify_node(self, state: GraphState) -> Dict:
        """Verify the preliminary analysis for legal soundness and citations."""
        prompt = f"""Review the following preliminary legal analysis to ensure it is strictly objective, professional, and includes exact citations to the source pages provided. Remove any informal language.

Preliminary Analysis:
{state['analysis']}

Please provide the final, polished legal insight ensuring proper markdown formatting."""
        
        response = self.llm.invoke([SystemMessage(content=LEGAL_SYSTEM_PROMPT), HumanMessage(content=prompt)])
        return {"verified_response": response.content}

    def respond_node(self, state: GraphState) -> Dict:
        """Compile the final response to be added to the messages state."""
        final_content = state["verified_response"] + DISCLAIMER
        return {"messages": [AIMessage(content=final_content)]}

    def invoke(self, messages: List[BaseMessage]):
        return self.graph.invoke({"messages": messages})
