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
