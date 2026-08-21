# 🤝 Contributing to ArchMCP

Thank you for your interest in contributing to **ArchMCP**! We welcome contributions from developers of all experience levels.

---

## 🛠️ Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/archmcp.git
   cd archmcp
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies in editable mode**:
   ```bash
   pip install -e .[dev]
   ```

4. **Run the test suite**:
   ```bash
   pytest -v
   ```

---

## 💡 How to Add New Features

### Adding a New MCP Tool
1. Define any new domain models in `src/archmcp/models/`.
2. Implement your core logic in `src/archmcp/services/`.
3. Register the `@server.tool()` in `src/archmcp/mcp/tools.py` with descriptive docstrings and parameter type annotations.
4. Add unit and integration tests in `tests/test_mcp.py`.

### Adding a New MCP Prompt
1. Open `src/archmcp/mcp/prompts.py`.
2. Use `@server.prompt()` to register the new workflow template.
3. Add a test verifying `server.get_prompt()` in `tests/test_mcp.py`.

### Adding New Ingestion Parsers
* Place new parsers (e.g. gRPC Protobuf parser, Backstage catalog connector, Prisma schema extractor) in `src/archmcp/ingestion/`.

---

## 🧪 Testing Guidelines

Before opening a pull request, make sure all tests pass:
```bash
python -m pytest
```

---

## 📝 Pull Request Process

1. Create a feature branch (`git checkout -b feat/my-new-tool`).
2. Commit your changes with clear, semantic commit messages (`git commit -m 'feat: add protobuf schema parser'`).
3. Push to your fork (`git push origin feat/my-new-tool`).
4. Open a Pull Request against `main` describing what changed and why.

---

## 📄 License
By contributing to ArchMCP, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
