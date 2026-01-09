#!/usr/bin/env python3
"""
Verification script for SynthClip deployment
Run this to verify that all components work correctly
"""
import sys
import os

def check_syntax():
    """Check Python syntax"""
    try:
        with open('web_app.py', 'r') as f:
            code = f.read()
        compile(code, 'web_app.py', 'exec')
        print("✅ web_app.py syntax is valid")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in web_app.py: {e}")
        return False

def check_imports():
    """Check that all imports work"""
    try:
        # Test basic imports
        import asyncio
        import aiohttp
        import aiofiles
        from fastapi import FastAPI
        from config import Config

        # Test app import
        from web_app import app

        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def check_indentation():
    """Check for indentation issues"""
    try:
        with open('web_app.py', 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            # Check for mixed tabs and spaces
            if '\t' in line and ' ' in line[:len(line) - len(line.lstrip())]:
                print(f"⚠️  Mixed tabs/spaces in line {i}: {repr(line[:50])}")
            # Check for unusual indentation
            stripped = line.rstrip('\n\r')
            if stripped and not stripped[0].isspace() and stripped.startswith((' ' * 4, ' ' * 8, ' ' * 12, ' ' * 16)):
                indent_level = len(line) - len(line.lstrip())
                if indent_level not in [4, 8, 12, 16, 20, 24, 28, 32]:
                    print(f"⚠️  Unusual indentation ({indent_level} spaces) in line {i}")

        print("✅ Indentation check completed")
        return True
    except Exception as e:
        print(f"❌ Indentation check failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🔍 SynthClip Deployment Verification")
    print("=" * 50)

    all_good = True

    # Check syntax
    if not check_syntax():
        all_good = False

    # Check imports
    if not check_imports():
        all_good = False

    # Check indentation
    if not check_indentation():
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All checks passed! SynthClip is ready for deployment.")
        print("\n📋 Deployment checklist:")
        print("  ✅ Syntax validation")
        print("  ✅ Import verification")
        print("  ✅ Indentation check")
        print("  🚀 Ready for Railway deployment")
    else:
        print("❌ Some checks failed. Please fix the issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()