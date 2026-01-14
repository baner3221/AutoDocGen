# Git Commit Instructions

You have made several critical fixes to the codebase:
1.  **Token Limit Fix**: Increased context window for large files.
2.  **Concurrency Control**: Added `--workers` flag to prevent crashing.
3.  **Visual Feedback**: Enabled live LLM output printing.
4.  **Bug Fixes**: Resolved variable scope issues in `main.py`.

## 1. Status Check
See which files changed:
```powershell
git status
```

## 2. Stage Changes
Add all modified files to the "stage":
```powershell
git add .
```

## 3. Commit Code
Save the snapshot with a descriptive message:
```powershell
git commit -m "Fix: Increased token limits, added --workers flag, and enabled verbose output"
```

## 4. Push to GitHub
Upload changes to the remote repository (master branch):
```powershell
git push origin master
```

---
*Note: If `git` is still not found, remember to restart your terminal or use the full path `& "C:\Program Files\Git\cmd\git.exe" ...`*
