# Gemini API Library

This is a utility library for accessing Gemini models and configuring tool calling to given
python function references.

## Uses the Latest `google-genai`

Absolutely FORBIDS usage of the legacy `google-generativeai` SDK.

You MUST use the new SDK based on `from google import genai`.

DO NOT USE VERTEX AI

## No Streaming

There's no point supporting streaming. Don't add code for that.

