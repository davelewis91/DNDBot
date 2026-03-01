from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama


def get_llm(
    model: str = "llama3:8b",
    temperature: float = 0.7,
    provider: str = "ollama",
) -> BaseChatModel:
    """
    Get a configured LLM client.

    Parameters
    ----------
    model : str
        Model name (e.g. "llama3:8b" or "claude-haiku-4-5-20251001")
    temperature : float
        Sampling temperature (0.0-1.0)
    provider : str
        Either "ollama" (local, free) or "anthropic" (cloud, paid)

    Returns
    -------
    BaseChatModel
        Configured LangChain chat model
    """
    if provider == "ollama":
        return ChatOllama(model=model, temperature=temperature)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unknown provider: {provider!r}. Use 'ollama' or 'anthropic'.")
