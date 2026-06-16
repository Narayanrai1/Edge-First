import ollama

class LLMServiceError(Exception):
    pass


class LLMService:

    SYSTEM_INSTRUCTION = (
        "You are an enterprise knowledge assistant. Answer the user's question "
        "using ONLY the context provided below. If the context does not contain "
        "the answer, say you don't have enough information -- do not invent facts."
    )

    def __init__(self, model: str = "phi3", host: str = "http://localhost:11434"):
        
        self.model = model
        self.client = ollama.Client(host=host)

    def _build_prompt(self, context_chunks: list, question: str) -> str:
        if context_chunks:
            context_block = "\n\n".join(
                f"[Source: {c.get('source', 'unknown')}]\n{c['text']}"
                for c in context_chunks
            )
        else:
            context_block = "(No relevant context was found in the knowledge base.)"

        return (
            f"{self.SYSTEM_INSTRUCTION}\n\n"
            f"--- CONTEXT ---\n{context_block}\n\n"
            f"--- QUESTION ---\n{question}\n\n"
            f"--- ANSWER ---\n"
        )

    def generate_answer(self, context_chunks: list, question: str) -> str:
        
        prompt = self._build_prompt(context_chunks, question)

        try:
            response = self.client.generate(model=self.model, prompt=prompt)

            return response["response"].strip()

        except ConnectionError as e:

            raise LLMServiceError(
                "Could not reach the Ollama server at the configured host. "
                "Is Ollama installed and running? Try `ollama serve`."
            ) from e

        except ollama.ResponseError as e:

            if getattr(e, "status_code", None) == 404:
                raise LLMServiceError(
                    f"The model '{self.model}' is not available in Ollama. "
                    f"Pull it first with: ollama pull {self.model}"
                ) from e
            raise LLMServiceError(f"Ollama returned an error: {e}") from e

        except Exception as e:

            raise LLMServiceError(f"Unexpected error talking to the LLM: {e}") from e

    def is_available(self) -> bool:

        try:
            self.client.list() 
            return True
        except Exception:
            return False
