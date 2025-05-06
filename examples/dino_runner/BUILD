load("//rules_natty:defs.bzl", "natty_java_binary", "natty_java_library")
load("@pypi//:requirements.bzl", "requirement")

# Test out this Natty program using the following command:
#
#   $ bazel run examples/dino_runner --action_env=LLM_API_KEY=<your own Gemini API key>
#
# (Note: you'll need your own Gemini API Key)
natty_java_binary(
    name = "dino_runner",
    src = "dino_runner.md",
    deps = [
        ":game_loop",
        ":input_handler",
        ":physics_engine",
        ":game_world",
        ":dinosaur",
        ":obstacle",
        ":renderer",
        ":sound",
        ":score",
    ],
    max_output_tokens = 16000,
    llm_model = "gemini-2.5-pro-exp-03-25",
)

# Game loop component
natty_java_library(
    name = "game_loop",
    src = "game_loop.md",
    deps = [
        ":dinosaur", 
        ":obstacle",
        ":score",
    ],
    max_output_tokens = 16000,
    llm_model = "gemini-2.5-pro-exp-03-25",
)

# Input handler component
natty_java_library(
    name = "input_handler",
    src = "input_handler.md",
)

# Physics engine component
natty_java_library(
    name = "physics_engine",
    src = "physics_engine.md",
    deps = [
        ":dinosaur",
        ":obstacle",
    ],
)

# Game world component
natty_java_library(
    name = "game_world",
    src = "game_world.md",
    deps = [
        ":obstacle",
    ],
)

# Dinosaur character component
natty_java_library(
    name = "dinosaur",
    src = "dinosaur.md",
)

# Obstacles component
natty_java_library(
    name = "obstacle",
    src = "obstacle.md",
)

# Renderer component
natty_java_library(
    name = "renderer",
    src = "renderer.md",
    deps = [
        ":dinosaur",
        ":obstacle",
        ":game_world",
        ":score",
    ],
    max_output_tokens = 16000,
    llm_model = "gemini-2.5-pro-exp-03-25",
)

# Sound system component
natty_java_library(
    name = "sound",
    src = "sound.md",
)

# Score system component
natty_java_library(
    name = "score",
    src = "score.md",
)