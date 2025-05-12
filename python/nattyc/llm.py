import logging
from dataclasses import dataclass
from typing import cast

from google import genai
from google.genai.types import (
    GenerateContentConfig,
    HarmBlockThreshold,
    HarmCategory,
    SafetySetting,
)
from pydantic import BaseModel


@dataclass
class LlmResponse:
    """Data class to standardize LLM response format."""

    parsed: BaseModel
    model: str
    usage: dict[str, int | None]
    finish_reason: str | None


async def call_llm(
    *,
    system_prompt: str,
    english_description: str,
    model_name: str,
    api_key: str,
    response_schema: type[BaseModel],
    temperature: float = 0.2,
    max_output_tokens: int = 8192,
) -> LlmResponse:
    """Call the Gemini API to generate code.

    Args:
        prompt: The formatted prompt to send to the LLM
        model_name: The specific Gemini model to use
        api_key: API key for authentication
        temperature: Sampling temperature (lower = more deterministic)
        max_output_tokens: Maximum tokens in the response

    Returns:
        An LlmResponse object containing the generated code and metadata

    Raises:
        ValueError: If required parameters are missing or invalid
        RuntimeError: If the API call fails
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"--- SYSTEM PROMPT for {model_name} ---")
    logger.debug(
        system_prompt
    )  # Use debug to avoid showing the entire prompt in normal operation
    logger.debug("--- END SYSTEM PROMPT ---")

    if not api_key:
        raise ValueError("Error: LLM_API_KEY not set.")

    try:
        # Create a client instance
        client = genai.Client(api_key=api_key)

        # Generate the content
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=english_description,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                candidate_count=1,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                # Set up safety settings - allow code generation
                safety_settings=[
                    SafetySetting(
                        category=category,
                        threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    )
                    for category in HarmCategory
                    if category is not HarmCategory.HARM_CATEGORY_UNSPECIFIED
                ],
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )

        # Handle potential content filtering
        if response.candidates and response.candidates[0].finish_reason == "SAFETY":
            raise RuntimeError("Content was filtered due to safety concerns")

        if not response.parsed:
            raise RuntimeError("LLM Response failed to parse to required schema.")

        # Create usage stats dictionary (estimate, as Gemini might not provide exact counts)
        if response.usage_metadata:
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "cached_tokens": response.usage_metadata.cached_content_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }
        else:
            usage = {}

        # Get finish reason
        finish_reason = None
        if response.candidates:
            finish_reason = response.candidates[0].finish_reason

        return LlmResponse(
            parsed=cast(BaseModel, response.parsed),
            model=model_name,
            usage=usage,
            finish_reason=finish_reason,
        )

    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        raise RuntimeError(f"Failed to generate code: {str(e)}")
