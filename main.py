import os
import subprocess
import textwrap
import logging as LOG

def get_repo_structure(path=".", max_depth=3):
    structure = []
    base_depth = path.rstrip(os.sep).count(os.sep)

    for root, dirs, files in os.walk(path):
        if ".git" not in root:
            depth = root.count(os.sep) - base_depth
            if depth >= max_depth:
                dirs[:] = [] 
                continue

            indent = " " * 4 * depth
            structure.append(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 4 * (depth + 1)
            for f in files:
                structure.append(f"{subindent}{f}")

    return "\n".join(structure)


def query_ollama(prompt, model="codellama"):
    LOG.info("Sending prompt to Ollama")
    try:
        process = subprocess.Popen(
            ["ollama", "run", model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        process.stdin.write(prompt)
        process.stdin.close()

        output_lines = []
        LOG.info("Ollama output:")
        for line in process.stdout:
            LOG.debug(line) 
            output_lines.append(line)

        stderr = process.stderr.read()
        if stderr:
            LOG.error("Ollama ERROR:")
            LOG.error(stderr)

        process.wait()
        LOG.info("Ollama finished.")

        return "".join(output_lines).strip()

    except Exception as e:
        LOG.error(f"Failed to run ollama: {e}")
        return ""


def generate_docs(repo_path, model="codellama"):
    LOG.info("Scanning repository structure...")
    structure = get_repo_structure(repo_path)
    LOG.info("Repo structure generated:")

    prompt = textwrap.dedent(f"""
    You are a codebase documentation generator.
    Analyze the following repository structure:
    {structure}
    1. Provide a high-level explanation of the architecture.
    2. Summarize each folder/module purpose.
    3. Suggest an architecture diagram in Mermaid.js syntax.
    4. Output in Markdown format.
    """)

    LOG.info("Triggering LLM...")
    doc_text = query_ollama(prompt, model=model)

    if not doc_text.strip():
        LOG.warning("No output received from Ollama.")
        return

    docs_path = os.path.join(repo_path, "docs")
    os.makedirs(docs_path, exist_ok=True)
    output_file = os.path.join(docs_path, "README.md")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(doc_text)

    LOG.info(f"Documentation generated at: {output_file}")


if __name__ == "__main__":
    repo = r"F:\CodeBase\DocLLM"
    model = "codellama:7b"
    LOG.info(f"Starting documentation generator with {model}")
    generate_docs(repo, model)
