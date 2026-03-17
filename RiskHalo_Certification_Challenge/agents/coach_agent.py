import os
from typing import TypedDict, List
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from rag.vector_store import RiskHaloVectorStore
from agents.tools import TavilySearchTool


load_dotenv()


# -----------------------------
# Define Agent State
# -----------------------------
class CoachState(TypedDict):
    query: str
    query_embedding: List[float]
    retrieved_docs: List[str]
    external_context: str
    response: str


# -----------------------------
# Initialize Models and tools
# -----------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = RiskHaloVectorStore()

tavily_tool = TavilySearchTool()


# -----------------------------
# Node: Embed Query
# -----------------------------
def embed_query(state: CoachState):
    embedding = embeddings.embed_query(state["query"])
    return {"query_embedding": embedding}


# ---------------------------------------
# Node: Retrieve Sessions from vector DB
# ---------------------------------------
def retrieve_sessions(state: CoachState):
    results = vector_store.collection.query(
        query_embeddings=[state["query_embedding"]],
        n_results=3
    )

    documents = results.get("documents", [[]])[0]

    #print(f"Retrieved documents: {documents}")
    return {"retrieved_docs": documents}


# --------------------------------------------------
# Node: Decide Whether to Use External Tool
# --------------------------------------------------
def decide_tool_usage(state: CoachState):

    query = state["query"].lower()

    tool_trigger_keywords = [
        "why",
        "research",
        "behavioral finance",
        "psychology",
        "study",
        "studies",
        "explain",
        "theory"
    ]

    if any(keyword in query for keyword in tool_trigger_keywords):
        return "use_tool"

    return "skip_tool"

# --------------------------------------------------
# Node: Call Tavily Tool
# --------------------------------------------------
def call_tavily(state: CoachState):

    print(f"Calling Tavily Tool with query: {state['query']}")
    external_context = tavily_tool.search(state["query"])

    return {"external_context": external_context}


# -----------------------------
# Node: Generate Response
# -----------------------------
def generate_response(state: CoachState):

    retrieved_context = "\n\n".join(state.get("retrieved_docs", []))
    external_context = state.get("external_context", "")

    system_prompt = """
    You are RiskHalo, a performance-focused trading execution coach.

    Your role is to answer ONLY questions about:
    - trading performance and execution,
    - behavioral patterns and trading psychology,
    - risk management and expectancy,
    - discipline and rule adherence in trading.

    You must strictly refuse to answer questions that are:
    - about the user's identity (e.g. name, age, location),
    - about unrelated personal details or biography,
    - about topics outside trading, markets, or trading psychology.

    When a question is out of scope, you MUST respond briefly that you
    can only discuss trading behavior, risk discipline and performance,
    and that you do not know personal details about the user.

    Core Principles:
    - Provide disciplined, data-backed feedback.
    - Base your reasoning ONLY on the retrieved session context.
    - Do not invent metrics or assume missing data.
    - Do not predict markets or discuss price direction.
    - Focus strictly on execution quality, behavioral patterns, risk management, and performance consistency.

    Response Guidelines (for in-scope questions only):
    - Start with a clear conclusion.
    - Reference relevant session trends when available.
    - Interpret severity, expectancy shifts, and behavioral states.
    - Maintain a professional, performance-oriented tone.
    - Avoid exaggeration or emotional language.
    - If context is insufficient, state that explicitly.

    Your goal is to help the trader improve execution discipline and behavioral consistency.
    """

    updated_system_prompt_with_output_structure = """
    You are RiskHalo, a performance-focused trading execution coach.

    Your role is to analyze behavioral trading patterns using retrieved session summaries.

    You must follow ALL rules below strictly.

    Core Principles:
    - Base your reasoning ONLY on the retrieved session context.
    - Do NOT invent metrics or assume missing data.
    - Do NOT predict markets or discuss price direction.
    - Focus strictly on execution quality, behavioral patterns, risk management, and consistency.
    - Maintain a disciplined, professional, performance-oriented tone.
    - Avoid exaggeration or emotional language.

    If retrieved context is insufficient to answer the question,
    explicitly state that the available session data is insufficient.

    You MUST structure every response in exactly the following 4 sections:

    1. Summary Insight
    - Provide a clear, direct answer to the user's question.
    - State the primary behavioral finding.

    2. Supporting Evidence from Sessions
    - Reference relevant behavioral states, severity trends, expectancy shifts, or financial impact.
    - Only use information present in the retrieved sessions.

    3. Behavioral Interpretation
    - Explain what the observed pattern means in terms of execution discipline.
    - Focus on behavioral mechanisms (e.g., escalation, hesitation, stability, recovery).

    4. Performance Recommendation
    - Provide one or two concrete, execution-focused improvement suggestions.
    - Keep recommendations realistic and rule-based.
    """

    user_prompt = f"""
    User Question:
    {state['query']}

    Retrieved Behavioral Sessions:
    {retrieved_context}

    External Knowledge (if any):
    {external_context}

    Provide a structured, performance-coach style response.
    """

    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])

    return {"response": response.content}


# -----------------------------
# Build LangGraph
# -----------------------------
def build_coach_agent():

    workflow = StateGraph(CoachState)

    workflow.add_node("embed_query", embed_query)
    workflow.add_node("retrieve_sessions", retrieve_sessions)
    workflow.add_node("call_tavily", call_tavily)
    workflow.add_node("generate_response", generate_response)

    workflow.set_entry_point("embed_query")

    workflow.add_edge("embed_query", "retrieve_sessions")
    workflow.add_conditional_edges(
        "retrieve_sessions",
        decide_tool_usage,
        {
            "use_tool": "call_tavily",
            "skip_tool": "generate_response"
        }
    )

    workflow.add_edge("call_tavily", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


# -----------------------------
# Public Interface
# -----------------------------
def ask_coach(question: str):

    agent = build_coach_agent()

    result = agent.invoke({"query": question})

    return result["response"]


# -----------------------------
# Streaming: get state then stream LLM
# -----------------------------
SYSTEM_PROMPT = """
You are RiskHalo, a performance-focused trading execution coach.

Your role is to answer ONLY questions about:
- trading performance and execution,
- behavioral patterns and trading psychology,
- risk management and expectancy,
- discipline and rule adherence in trading.

You must strictly refuse to answer questions that are:
- about the user's identity (e.g. name, age, location),
- about unrelated personal details or biography,
- about topics outside trading, markets, or trading psychology.

When a question is out of scope, you MUST respond briefly that you
can only discuss trading behavior, risk discipline, and performance,
and that you do not know personal details about the user.

Your role is to analyze behavioral trading patterns using retrieved session summaries.

You must follow ALL rules below strictly.

Core Principles:
- Base your reasoning ONLY on the retrieved session context.
- Do NOT invent metrics or assume missing data.
- Do NOT predict markets or discuss price direction.
- Focus strictly on execution quality, behavioral patterns, risk management, and consistency.
- Maintain a disciplined, professional, performance-oriented tone.
- Avoid exaggeration or emotional language.

If retrieved context is insufficient to answer the question,
explicitly state that the available session data is insufficient.

You MUST structure every response in exactly the following 4 sections:

1. Summary Insight
- Provide a clear, direct answer to the user's question.
- State the primary behavioral finding.

2. Supporting Evidence from Sessions
- Reference relevant behavioral states, severity trends, expectancy shifts, or financial impact.
- Only use information present in the retrieved sessions.

3. Behavioral Interpretation
- Explain what the observed pattern means in terms of execution discipline.
- Focus on behavioral mechanisms (e.g., escalation, hesitation, stability, recovery).

4. Performance Recommendation
- Provide one or two concrete, execution-focused improvement suggestions.
- Keep recommendations realistic and rule-based.
"""


def get_coach_state(question: str) -> CoachState:
    """Run embed + retrieve + optional tavily; return state for generation."""
    state = {"query": question}
    state = {**state, **embed_query(state)}
    state = {**state, **retrieve_sessions(state)}
    if decide_tool_usage(state) == "use_tool":
        state = {**state, **call_tavily(state)}
    else:
        state = {**state, "external_context": ""}
    return state


def stream_coach_response(question: str):
    """Yield LLM response chunks for streaming."""
    state = get_coach_state(question)
    retrieved_context = "\n\n".join(state.get("retrieved_docs", []))
    external_context = state.get("external_context", "")

    user_prompt = f"""
User Question:
{state['query']}

Retrieved Behavioral Sessions:
{retrieved_context}

External Knowledge (if any):
{external_context}

Provide a structured, performance-coach style response.
"""

    for chunk in llm.stream([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]):
        if chunk.content:
            yield chunk.content