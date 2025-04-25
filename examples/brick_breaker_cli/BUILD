load("//rules_natty:defs.bzl", "natty_binary", "natty_library")
load("@pypi//:requirements.bzl", "requirement")

# Test out this Natty program using the following command:
#
#   $ bazel run examples/brick_breaker_cli --action_env=LLM_API_KEY=<your own Gemini API key>
#
# (Note: you'll need your own Gemini API Key)
natty_binary(
    name = "brick_breaker_cli",
    src = "brick_breaker_cli.md",
    deps = [":ball", ":obstacle", ":sound"],
)

# TODO(steving) random out of place test, drop this or move it.
natty_binary(
    name = "gemini_api_cli",
    src = "gemini_api_cli.md",
    deps = [":gemini_api_lib", "//examples/pretty_printer_cli:pretty_print"],
    py_deps = [
        requirement("google-genai"),
    ],
    docs = ["gemini_api_docs.txt"],
)

# TODO(steving) random out of place test, drop this or move it.
natty_library(
    name = "gemini_api_lib",
    src = "gemini_api_lib.md",
    py_deps = [
        requirement("google-genai"),
    ],
    docs = ["gemini_api_docs.txt"],
)

natty_library(
    name = "ball",
    src = "ball.md",
)

natty_library(
    name = "obstacle",
    src = "obstacle.md",
)

natty_library(
    name = "sound",
    src = "sound.md",
    py_deps = [
        requirement("numpy"),
        requirement("simpleaudio"),
    ],
)
