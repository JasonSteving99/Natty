load("//rules_natty:defs.bzl", "natty_binary", "natty_library")
load("@pypi//:requirements.bzl", "requirement")

# Test out this Natty program using the following command:
#
#   $ bazel run //examples/gemini_api_cli --action_env=LLM_API_KEY=<your own Gemini API key>
#
# (Note: you'll need your own Gemini API Key)
natty_binary(
    name = "gemini_api_cli",
    src = "gemini_api_cli.md",
    deps = [":gemini_api_lib", "//examples/pretty_printer_cli:pretty_print"],
    py_deps = [
        requirement("google-genai"),
    ],
    docs = ["gemini_api_docs.txt"],
)

natty_library(
    name = "gemini_api_lib",
    src = "gemini_api_lib.md",
    py_deps = [
        requirement("google-genai"),
    ],
    docs = ["gemini_api_docs.txt"],
)
