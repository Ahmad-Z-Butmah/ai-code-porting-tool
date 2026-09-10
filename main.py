import os
import io
import sys
import shutil
import subprocess
import tempfile
import time

from dotenv import load_dotenv
from google import genai
import gradio as gr

from system_info import retrieve_system_info
from styles import CSS


# =========================
# Environment
# =========================

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in the .env file")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.6-flash"


# =========================
# System Information
# =========================

system_info = retrieve_system_info()


# =========================
# Example Python Code
# =========================

python_example = """def fibonacci(n):
    a, b = 0, 1

    for _ in range(n):
        a, b = b, a + b

    return a

print(fibonacci(40))
"""


# =========================
# AI Code Conversion
# =========================

def port_code(python_code, language):

    if not python_code.strip():
        return ""

    system_prompt = f"""
You are an expert software engineer specializing in high-performance code.

Convert the provided Python program into high-performance {language}.

Requirements:
- Produce identical output to the Python program.
- Optimize for runtime performance.
- Preserve the behavior of the original program.
- Produce complete executable code.
- Do not include markdown code fences.
- Do not include explanations.
- Return only the {language} source code.
"""

    user_prompt = f"""
Convert the following Python code to {language}.

System information:

{system_info}

Python code:

{python_code}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=system_prompt + "\n\n" + user_prompt
    )

    code = response.text or ""

    code = (
        code
        .replace("```cpp", "")
        .replace("```c++", "")
        .replace("```rust", "")
        .replace("```", "")
        .strip()
    )

    return code


# =========================
# Run Python
# =========================

def run_python(code):

    if not code.strip():
        return "No Python code provided."

    buffer = io.StringIO()
    old_stdout = sys.stdout

    start = time.perf_counter()

    try:
        sys.stdout = buffer

        globals_dict = {
            "__builtins__": __builtins__
        }

        exec(code, globals_dict)

        execution_time = time.perf_counter() - start

        output = buffer.getvalue()

        return (
            f"{output}\n"
            f"Execution time: {execution_time:.6f} seconds"
        )

    except Exception as error:
        return f"Python error:\n{error}"

    finally:
        sys.stdout = old_stdout


# =========================
# C++ Compile + Run
# =========================

def run_cpp(code):

    if not code.strip():
        return "No C++ code provided."

    compiler = shutil.which("g++")

    if not compiler:
        return (
            "C++ compiler not found.\n\n"
            "Install MinGW-w64 / g++ and make sure g++ is available in PATH."
        )

    with tempfile.TemporaryDirectory() as temp_dir:

        source_file = os.path.join(temp_dir, "main.cpp")
        executable = os.path.join(temp_dir, "main.exe")

        with open(source_file, "w", encoding="utf-8") as file:
            file.write(code)

        compile_command = [
            compiler,
            source_file,
            "-O3",
            "-march=native",
            "-std=c++17",
            "-o",
            executable
        ]

        try:

            compile_result = subprocess.run(
                compile_command,
                capture_output=True,
                text=True,
                timeout=60
            )

            if compile_result.returncode != 0:
                return (
                    "C++ compilation failed:\n\n"
                    + compile_result.stderr
                )

            start = time.perf_counter()

            run_result = subprocess.run(
                [executable],
                capture_output=True,
                text=True,
                timeout=60
            )

            execution_time = time.perf_counter() - start

            if run_result.returncode != 0:
                return (
                    "C++ runtime error:\n\n"
                    + run_result.stderr
                )

            return (
                f"{run_result.stdout}\n"
                f"Execution time: {execution_time:.6f} seconds"
            )

        except subprocess.TimeoutExpired:
            return "Execution timed out."


# =========================
# Rust Compile + Run
# =========================

def run_rust(code):

    if not code.strip():
        return "No Rust code provided."

    compiler = shutil.which("rustc")

    if not compiler:
        return (
            "Rust compiler not found.\n\n"
            "Install Rust using rustup and make sure rustc is available in PATH."
        )

    with tempfile.TemporaryDirectory() as temp_dir:

        source_file = os.path.join(temp_dir, "main.rs")
        executable = os.path.join(temp_dir, "main.exe")

        with open(source_file, "w", encoding="utf-8") as file:
            file.write(code)

        compile_command = [
            compiler,
            source_file,
            "-C",
            "opt-level=3",
            "-C",
            "target-cpu=native",
            "-o",
            executable
        ]

        try:

            compile_result = subprocess.run(
                compile_command,
                capture_output=True,
                text=True,
                timeout=60
            )

            if compile_result.returncode != 0:
                return (
                    "Rust compilation failed:\n\n"
                    + compile_result.stderr
                )

            start = time.perf_counter()

            run_result = subprocess.run(
                [executable],
                capture_output=True,
                text=True,
                timeout=60
            )

            execution_time = time.perf_counter() - start

            if run_result.returncode != 0:
                return (
                    "Rust runtime error:\n\n"
                    + run_result.stderr
                )

            return (
                f"{run_result.stdout}\n"
                f"Execution time: {execution_time:.6f} seconds"
            )

        except subprocess.TimeoutExpired:
            return "Execution timed out."


# =========================
# Run Generated Code
# =========================

def run_generated(code, language):

    if language == "C++":
        return run_cpp(code)

    if language == "Rust":
        return run_rust(code)

    return "Unsupported language."


# =========================
# Update Editor Language
# =========================

def change_language(language):

    editor_language = "cpp" if language == "C++" else "rust"

    return gr.update(
        label=f"{language} (generated)",
        language=editor_language
    )


# =========================
# Gradio UI
# =========================

with gr.Blocks(
    css=CSS,
    title="AI Code Porting & Performance Tool"
) as app:

    gr.Markdown(
        """
# AI Code Porting & Performance Tool

Convert Python code into optimized C++ or Rust using Gemini,
then run both versions and compare their results and execution time.
"""
    )

    language = gr.Dropdown(
        choices=[
            "C++",
            "Rust"
        ],
        value="C++",
        label="Target Language"
    )

    with gr.Row():

        with gr.Column():

            python_code = gr.Code(
                label="Python Code",
                value=python_example,
                language="python",
                lines=22
            )

            run_python_button = gr.Button(
                "Run Python"
            )

            python_output = gr.Textbox(
                label="Python Result",
                lines=8
            )

        with gr.Column():

            generated_code = gr.Code(
                label="C++ (generated)",
                language="cpp",
                lines=22
            )

            with gr.Row():

                convert_button = gr.Button(
                    "Convert with Gemini",
                    elem_classes=["convert-btn"]
                )

                run_generated_button = gr.Button(
                    "Run Generated Code"
                )

            generated_output = gr.Textbox(
                label="Generated Code Result",
                lines=8
            )

    language.change(
        fn=change_language,
        inputs=language,
        outputs=generated_code
    )

    convert_button.click(
        fn=port_code,
        inputs=[
            python_code,
            language
        ],
        outputs=generated_code
    )

    run_python_button.click(
        fn=run_python,
        inputs=python_code,
        outputs=python_output
    )

    run_generated_button.click(
        fn=run_generated,
        inputs=[
            generated_code,
            language
        ],
        outputs=generated_output
    )


if __name__ == "__main__":
    app.launch(inbrowser=True)