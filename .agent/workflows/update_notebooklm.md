---
description: Update NotebookLM Knowledge Base with latest code
---

1. [Run Script] Generate fresh codebase dump
   - Run `python3 scripts/prepare_kb.py` to create `full_codebase.txt`.
   
2. [Process] Upload to NotebookLM
   - Use `notebooklm-mcp` tool.
   - Resource: `aa483185-30ad-4a9b-bf58-f2736cb789e5` (Telegram Calendar Bot Development).
   - Tool `source_add(notebook_id="...", file_path=".../full_codebase.txt", source_type="file")`

3. [Finish] Notify User
   - Confirm upload is complete.
