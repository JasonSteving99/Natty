load("@rules_python//python:py_binary.bzl", "py_binary")
load("@pypi//:requirements.bzl", "requirement")


py_binary(
  name = "main",
  srcs = ["main.py"],
  deps = [
    requirement("asyncclick"),
    requirement("google-genai"),
    requirement("pydantic"),
  ]
)