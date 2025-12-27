#!/usr/bin/env python3
"""
Test script for ai_generator.py changes
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Test the _manage_cache_size function
def test_manage_cache_size():
    from backend.app.ai_generator import _manage_cache_size, AI_CACHE, _MAX_CACHE_SIZE

    # Clear cache
    AI_CACHE.clear()

    # Add more than max entries
    for i in range(_MAX_CACHE_SIZE + 50):
        AI_CACHE[f"key_{i}"] = f"value_{i}"

    initial_size = len(AI_CACHE)
    print(f"Cache size before management: {initial_size}")

    # Call manage cache size
    _manage_cache_size()

    final_size = len(AI_CACHE)
    print(f"Cache size after management: {final_size}")

    # Verify size is at or below max
    assert final_size <= _MAX_CACHE_SIZE, f"Cache size {final_size} exceeds max {_MAX_CACHE_SIZE}"
    print("✓ Cache size management test passed")

# Test input validation in get_unified_analysis
def test_input_validation():
    from backend.app.ai_generator import get_unified_analysis

    # Test with invalid skills (non-list)
    try:
        result = get_unified_analysis("invalid_skills", "Software Engineer")
        print("✗ Input validation failed - should have raised exception for non-list skills")
        return False
    except RuntimeError as e:
        if "Invalid user skills format" in str(e):
            print("✓ Input validation passed for non-list skills")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"✗ Unexpected exception type: {e}")
        return False

    # Test with valid inputs (should not raise)
    try:
        # This will likely fail due to AI unavailability, but should not fail due to input validation
        result = get_unified_analysis(["Python", "JavaScript"], "Software Engineer")
        print("✓ Input validation passed for valid inputs")
    except RuntimeError as e:
        if "AI unavailable" in str(e):
            print("✓ Input validation passed - AI unavailable as expected")
        else:
            print(f"✗ Unexpected RuntimeError: {e}")
            return False
    except Exception as e:
        print(f"✗ Unexpected exception: {e}")
        return False

    return True

if __name__ == "__main__":
    print("Testing ai_generator.py changes...")

    try:
        test_manage_cache_size()
        if test_input_validation():
            print("\n✓ All tests passed!")
        else:
            print("\n✗ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        sys.exit(1)
