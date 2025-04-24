load("//rules_natty:defs.bzl", "natty_binary", "natty_library")

# Test out this Natty program using the following command:
#
#   $ bazel run examples/hello_natty:cli_printer --action_env=LLM_API_KEY=<your own Gemini API key>
#
# (Note: you'll need your own Gemini API Key)
natty_binary(
    name = "cli_printer",
    src = "cli_printer.md",
    deps = [":pretty_print"],
)

natty_library(
    name = "pretty_print",
    src = "pretty_print.md",
)
