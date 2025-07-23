# 📁 File Organization Guidelines

## 🚫 **DO NOT** place files in the root directory

The project root should only contain:
- `run_server.py` - Main server entry point
- `main.py` - FastAPI app definition  
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation
- `.env` - Environment variables
- `.gitignore` - Git ignore patterns
- Configuration folders (`src/`, `admin/`, `portal/`, etc.)

## ✅ **DO** place files in appropriate folders

### **Test Scripts** → `tests/`
```
tests/
├── test_brain_dump_session_ids.py
├── check_brain_dumps.py
├── test_api_direct.py
└── ...
```

### **Setup & Help Scripts** → `help-files/`
```
help-files/
├── SETUP.md
├── ARCHITECTURE.md
├── setup_guide.py
└── ...
```

### **Local Development** → `local-dev-resources/`
```
local-dev-resources/
├── cloudflared.exe
├── config.yml
├── start_tunnel.bat
└── ...
```

## 🔄 **Development Workflow**

1. **Creating test scripts**: Always create in `tests/` folder
2. **Debugging scripts**: Create in `tests/` with descriptive names
3. **Setup scripts**: Place in `help-files/` 
4. **Temporary files**: Use `temp/` folder (gitignored)

## 🛡️ **Prevention**

- `.gitignore` now blocks common patterns like `test_*.py` in root
- Use descriptive folder names
- Always check file location before committing
- Run `git status` to see what you're about to commit

## 🧹 **Cleanup Command**

If files get scattered again, run:
```bash
# Move test scripts
move test_*.py tests/
move check_*.py tests/
move debug_*.py tests/

# Move help scripts  
move setup_*.py help-files/
move *_guide.py help-files/

# Move local dev files
move *.bat local-dev-resources/
move config.yml local-dev-resources/
```
