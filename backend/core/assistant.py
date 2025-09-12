import requests
import json
import logging
import os

logging.getLogger("requests").setLevel(logging.ERROR)


class OllamaExtractor:
    def __init__(self, settings, base_url="http://localhost:8880", model=None):
        self.base_url = base_url
        self.model = model or settings.extraction_model
        # Store path; do not read or format yet
        self._prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "assistant_prompt.txt")
        self.response_schema = self._build_response_schema()  # JSON schema definition
        print(f"Using Ollama model: {self.model}")

    def _read_prompt_file(self):
        """Read raw prompt template text each call (allows live edits)."""
        try:
            with open(self._prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return (
                "Answer the user's question based on the provided context.\n\n"
                "USER QUERY: {query}\nCONTEXT: {context}\n\n"
                "Respond with JSON: {\"result\": \"your answer\", \"evidence\": {\"doc_name\": [], \"chunk_id\": []}}"
            )

    def _build_response_schema(self):
        """Define the enforced JSON response schema for the model."""
        return {
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "evidence": {
                    "type": "object",
                    "properties": {
                        "doc_name": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "chunk_id": {
                            "type": "array",
                            "items": {"type": ["string", "integer"]}
                        }
                    },
                    "required": ["doc_name", "chunk_id"],
                    "additionalProperties": False
                }
            },
            "required": ["result", "evidence"],
            "additionalProperties": False
        }

    def call_llm(
        self,
        prompt: str,
        response_format: dict = None,
        stream_response: bool = False,
    ):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream_response,
            "format": response_format,
        }

        if stream_response:
            response_text = ""
            with requests.post(f"{self.base_url}/api/generate", json=payload, stream=True) as response:
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        text = chunk.get('response', '')
                        response_text += text
                        print(text, end="", flush=True)
                        if chunk.get('done', False):
                            print()
                            break
            return response_text
        else:
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            result = response.json()
            return json.loads(result['response'])

    def extract_from_document(self, query, context):
        """Extract information using formatted context. Loads & formats prompt now."""
        base_template = self._read_prompt_file()
        try:
            full_prompt = base_template.format(query=query, context=context)
        except KeyError as e:
            # Guard against accidental braces in template
            safe_template = base_template.replace('{', '{{').replace('}', '}}')
            safe_template = safe_template.replace('{{query}}', '{query}').replace('{{context}}', '{context}')
            full_prompt = safe_template.format(query=query, context=context)

        try:
            raw = self.call_llm(full_prompt, response_format=self.response_schema, stream_response=False)
            data = raw if isinstance(raw, dict) else json.loads(raw)
        except Exception as e:
            return {"result": f"Error: {e}", "evidence": {"doc_name": [], "chunk_id": []}}

        return data
