# TODO: Update AI Generator to Use Gemini 2.5

- [x] Update backend/app/ai_generator.py: Change model from 'gemini-2.0-flash' to 'gemini-2.5-flash' in generate_ai_project_ideas function
- [x] Update backend/app/ai_generator.py: Change model from 'gemini-2.0-flash' to 'gemini-2.5-flash' in get_learning_paths_for_skills function
- [x] Update backend/app/ai_generator.py: Change model from 'gemini-2.0-flash' to 'gemini-2.5-flash' in get_unified_analysis function
- [x] Update backend/tests/test_ai_generator.py: Add time.sleep(5) after the AI call to avoid rate limits
- [x] Update backend/check_models.py: Change model from 'gemini-2.0-flash' to 'gemini-2.5-flash'
- [x] Run the test in test_ai_generator.py to verify a real AI response using 2.5-flash model
