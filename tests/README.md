# Test Files and Utilities

This folder contains various test files, diagnostic scripts, and development utilities for the getcute-app project.

## Test Files
- `test_*.py` - Automated test scripts for various components
- `check_*.py` - Database checking and validation scripts  
- `debug_*.py` - Debugging utilities for troubleshooting

## Diagnostic Scripts
- `brain_dump_media_summary.py` - Analyzes brain dump media content
- `quick_status.py` - Quick system status check
- `reminder_diagnostic.py` - Reminder system diagnostics
- `cleanup_test_sessions.py` - Cleans up test data from database
- `get_users.py` - Lists users in the database

## Usage
Run scripts from the project root directory:
```bash
python tests/check_brain_dumps.py
python tests/test_conversation_query.py
```

All scripts automatically handle import paths and should work from the project root directory.
