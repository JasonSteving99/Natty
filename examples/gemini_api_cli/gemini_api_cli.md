# Gemini API CLI REPL

This is a simple reple that runs in the command line that allows you to chat with Gemini. Each individual message is going to be separate.

## Uses the Latest `google-genai`

Absolutely FORBIDS usage of the legacy `google-generativeai` SDK.

You MUST use the new SDK based on `from google import genai`.

## TOOLS

Provide a single "Pretty Print" tool where if the user indicates that the LLM should respond with pretty
printed output, it will call the tool to render its response.

Include information in the system prompt that explicitly tells the model that any illusion to pretty printing or anything like that should make use of the tool, don't require the user to explicitly demand the tool call.
