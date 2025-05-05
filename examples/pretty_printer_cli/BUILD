load(
    "//rules_natty:defs.bzl", 
    "natty_binary", 
    "natty_library",
    "natty_java_binary", 
    "natty_java_library"
)

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
    visibility = ["//visibility:public"]
)

# Exact same as the above but codegen'ing Java.
natty_java_binary( name = "java_cli_printer",
    src = "cli_printer.md",
    deps = [":java_pretty_print"],
)

natty_java_library(
    name = "java_pretty_print",
    src = "pretty_print.md",
)
