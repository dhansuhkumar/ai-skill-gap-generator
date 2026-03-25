# backend/app/dashboard_routes.py
"""
Dashboard-specific routes for learning progress and data endpoints.
Works gracefully even if Supabase tables don't exist yet.
"""

import logging
from flask import Blueprint, request, jsonify, g, current_app
from .auth import token_required

logger = logging.getLogger(__name__)

dashboard = Blueprint('dashboard', __name__)

# In-memory fallback storage when Supabase tables don't exist
_local_progress = {}
_local_paths = {}


def _supabase_available():
    """Check if Supabase is available."""
    try:
        return current_app.supabase is not None
    except Exception:
        return False


@dashboard.route('/get_dashboard_data', methods=['POST'])
@token_required
def get_dashboard_data():
    """
    Get formatted dashboard data combining role analysis and learning path.
    Returns skill comparison, learning timeline, and summary stats.
    """
    data = request.get_json() or {}
    user_id = g.user['id']
    
    role_analysis = data.get('role_analysis', {})
    learning_path = data.get('learning_path', {})
    user_skills = data.get('user_skills', [])
    
    try:
        # Extract skills from learning path
        skills_data = learning_path.get('skills', {})
        projects = learning_path.get('projects', [])
        videos = learning_path.get('videos', [])
        
        # Build skill comparison data
        skill_comparison_items = []
        total_current = 0
        total_required = 0
        
        for skill_name, skill_info in skills_data.items():
            # Find user's current proficiency for this skill
            current_prof = 0
            source = 'manual'
            
            for user_skill in user_skills:
                if isinstance(user_skill, dict):
                    if user_skill.get('name', '').lower() == skill_name.lower():
                        current_prof = user_skill.get('confidence', 0)
                        source = user_skill.get('source', 'manual')
                        break
                elif isinstance(user_skill, str) and user_skill.lower() == skill_name.lower():
                    current_prof = 80  # Default confidence for matched skills
                    break
            
            required_prof = 80  # Default required proficiency
            gap = max(0, required_prof - current_prof)
            
            skill_comparison_items.append({
                'name': skill_name,
                'current_proficiency': current_prof,
                'required_proficiency': required_prof,
                'gap': gap,
                'source': source
            })
            
            total_current += current_prof
            total_required += required_prof
        
        # Calculate averages
        num_skills = len(skill_comparison_items)
        avg_current = round(total_current / num_skills, 1) if num_skills > 0 else 0
        avg_required = round(total_required / num_skills, 1) if num_skills > 0 else 80
        overall_gap = round(avg_required - avg_current, 1)
        
        # Build learning timeline with progress tracking
        learning_timeline = []
        for skill_name, skill_info in skills_data.items():
            steps = skill_info.get('steps', [])
            
            # Load saved progress
            completed_indices = set()
            try:
                saved_progress = _get_learning_progress(user_id, skill_name)
                completed_indices = set(saved_progress.get('completed_steps', []))
            except Exception:
                pass
            
            completed_steps = 0
            milestones_with_progress = []
            
            for idx, step in enumerate(steps):
                is_completed = idx in completed_indices
                if is_completed:
                    completed_steps += 1
                milestones_with_progress.append({
                    **step,
                    'completed': is_completed
                })
            
            progress_percentage = round((completed_steps / len(steps)) * 100) if steps else 0
            
            learning_timeline.append({
                'skill': skill_name,
                'summary': skill_info.get('summary', ''),
                'milestones': milestones_with_progress,
                'youtube_videos': skill_info.get('youtube_videos', []),
                'total_steps': len(steps),
                'completed_steps': completed_steps,
                'progress_percentage': progress_percentage
            })
        
        # GitHub insights placeholder (real data fetched separately by frontend)
        github_insights = {
            'available': False,
            'username': None,
            'total_repos': 0,
            'languages': []
        }
        
        # Count total videos from skill youtube_videos
        total_videos = 0
        for skill_name, skill_info in skills_data.items():
            total_videos += len(skill_info.get('youtube_videos', []))
        total_videos += len(videos)
        
        dashboard_data = {
            'skill_comparison': {
                'skills': skill_comparison_items,
                'average_current': avg_current,
                'average_required': avg_required,
                'overall_gap': overall_gap
            },
            'learning_timeline': learning_timeline,
            'github_insights': github_insights,
            'summary': {
                'total_skills': num_skills,
                'projects': len(projects),
                'videos': total_videos,
                'github_available': github_insights['available']
            }
        }
        
        return jsonify({
            'status': 'ok',
            'dashboard_data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error building dashboard data: {e}")
        return jsonify({'error': 'Failed to build dashboard data', 'details': str(e)}), 500


@dashboard.route('/save_learning_progress', methods=['POST'])
@token_required
def save_learning_progress():
    """
    Save learning step completion status.
    Uses Supabase if available, otherwise uses in-memory storage.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400
    
    user_id = g.user['id']
    skill_name = data.get('skill_name')
    step_index = data.get('step_index')
    completed = data.get('completed', False)
    
    if not skill_name or step_index is None:
        return jsonify({'error': 'skill_name and step_index are required'}), 400
    
    # Try Supabase first
    if _supabase_available():
        try:
            supabase = current_app.supabase
            
            # Get or create progress record
            existing = supabase.table('learning_progress').select('*').match({
                'user_id': user_id,
                'skill_name': skill_name
            }).execute()
            
            if existing.data:
                # Update existing record
                record = existing.data[0]
                completed_steps = set(record.get('completed_steps', []) or [])
                
                if completed:
                    completed_steps.add(step_index)
                else:
                    completed_steps.discard(step_index)
                
                supabase.table('learning_progress').update({
                    'completed_steps': list(completed_steps)
                }).eq('id', record['id']).execute()
            else:
                # Create new record
                completed_steps = [step_index] if completed else []
                supabase.table('learning_progress').insert({
                    'user_id': user_id,
                    'skill_name': skill_name,
                    'completed_steps': completed_steps
                }).execute()
            
            return jsonify({'status': 'ok', 'message': 'Progress saved to database'})
            
        except Exception as e:
            logger.warning(f"Supabase save failed (table may not exist), using in-memory: {e}")
    
    # Fallback to in-memory storage
    key = f"{user_id}:{skill_name}"
    if key not in _local_progress:
        _local_progress[key] = set()
    
    if completed:
        _local_progress[key].add(step_index)
    else:
        _local_progress[key].discard(step_index)
    
    return jsonify({'status': 'ok', 'message': 'Progress saved (in-memory)', 'note': 'Run SQL migration for persistence'})


@dashboard.route('/save_learning_path', methods=['POST'])
@token_required
def save_learning_path():
    """
    Save full learning path for persistence across sessions.
    Uses Supabase if available, otherwise uses in-memory storage.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400
    
    user_id = g.user['id']
    target_role = data.get('target_role')
    selected_skills = data.get('selected_skills', [])
    learning_path = data.get('learning_path', {})
    
    if not target_role:
        return jsonify({'error': 'target_role is required'}), 400
    
    # Try Supabase first
    if _supabase_available():
        try:
            supabase = current_app.supabase
            
            # Check if user already has a learning path
            existing = supabase.table('learning_paths').select('id').eq('user_id', user_id).execute()
            
            path_data = {
                'user_id': user_id,
                'target_role': target_role,
                'selected_skills': selected_skills,
                'learning_path': learning_path.get('learning_path', learning_path)
            }
            
            if existing.data:
                # Update existing
                supabase.table('learning_paths').update(path_data).eq('id', existing.data[0]['id']).execute()
            else:
                # Insert new
                supabase.table('learning_paths').insert(path_data).execute()
            
            return jsonify({'status': 'ok', 'message': 'Learning path saved to database'})
            
        except Exception as e:
            logger.warning(f"Supabase save failed (table may not exist), using in-memory: {e}")
    
    # Fallback to in-memory storage
    _local_paths[user_id] = {
        'target_role': target_role,
        'selected_skills': selected_skills,
        'learning_path': learning_path.get('learning_path', learning_path)
    }
    
    return jsonify({'status': 'ok', 'message': 'Learning path saved (in-memory)', 'note': 'Run SQL migration for persistence'})


@dashboard.route('/get_saved_learning_path', methods=['GET'])
@token_required
def get_saved_learning_path():
    """
    Get user's saved learning path if exists.
    Uses Supabase if available, otherwise uses in-memory storage.
    """
    user_id = g.user['id']
    
    # Try Supabase first
    if _supabase_available():
        try:
            supabase = current_app.supabase
            
            result = supabase.table('learning_paths').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                record = result.data[0]
                return jsonify({
                    'status': 'ok',
                    'has_saved_path': True,
                    'data': {
                        'target_role': record.get('target_role'),
                        'selected_skills': record.get('selected_skills', []),
                        'learning_path': record.get('learning_path', {}),
                        'updated_at': record.get('updated_at')
                    }
                })
        except Exception as e:
            logger.warning(f"Supabase query failed (table may not exist): {e}")
    
    # Check in-memory storage
    if user_id in _local_paths:
        return jsonify({
            'status': 'ok',
            'has_saved_path': True,
            'data': _local_paths[user_id]
        })
    
    # No saved path found
    return jsonify({
        'status': 'ok',
        'has_saved_path': False
    })


def _get_learning_progress(user_id: str, skill_name: str) -> dict:
    """Helper to get learning progress for a skill."""
    # Try Supabase first
    if _supabase_available():
        try:
            supabase = current_app.supabase
            result = supabase.table('learning_progress').select('*').match({
                'user_id': user_id,
                'skill_name': skill_name
            }).execute()

            if result.data:
                return result.data[0]
        except Exception:
            pass

    # Check in-memory storage
    key = f"{user_id}:{skill_name}"
    if key in _local_progress:
        return {'completed_steps': list(_local_progress[key])}

    return {'completed_steps': []}


# Learning path progress tracking (week/day/task based)
_local_path_progress = {}


@dashboard.route('/update_task_progress', methods=['POST'])
@token_required
def update_task_progress():
    """
    Upsert learning path task progress.
    Accepts { path_id, week_number, day_number, task_index, completed: bool }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    user_id = g.user['id']
    path_id = data.get('path_id')
    week_number = data.get('week_number')
    day_number = data.get('day_number')
    task_index = data.get('task_index')
    completed = data.get('completed', False)

    if path_id is None or week_number is None or day_number is None or task_index is None:
        return jsonify({'error': 'path_id, week_number, day_number, and task_index are required'}), 400

    # Try Supabase first
    if _supabase_available():
        try:
            supabase = current_app.supabase

            # Check if record exists
            existing = supabase.table('learning_progress').select('*').match({
                'user_id': user_id,
                'path_id': path_id,
                'week_number': week_number,
                'day_number': day_number
            }).execute()

            if existing.data:
                # Update existing record
                record = existing.data[0]
                completed_tasks = set(record.get('completed_tasks', []) or [])

                if completed:
                    completed_tasks.add(task_index)
                else:
                    completed_tasks.discard(task_index)

                supabase.table('learning_progress').update({
                    'completed_tasks': list(completed_tasks)
                }).eq('id', record['id']).execute()
            else:
                # Insert new record
                completed_tasks = [task_index] if completed else []
                supabase.table('learning_progress').insert({
                    'user_id': user_id,
                    'path_id': path_id,
                    'week_number': week_number,
                    'day_number': day_number,
                    'completed_tasks': completed_tasks
                }).execute()

            return jsonify({'status': 'ok', 'message': 'Task progress updated'})

        except Exception as e:
            logger.warning(f"Supabase update failed, using in-memory: {e}")

    # Fallback to in-memory storage
    key = f"{user_id}:{path_id}:{week_number}:{day_number}"
    if key not in _local_path_progress:
        _local_path_progress[key] = set()

    if completed:
        _local_path_progress[key].add(task_index)
    else:
        _local_path_progress[key].discard(task_index)

    return jsonify({'status': 'ok', 'message': 'Task progress saved (in-memory)'})


@dashboard.route('/get_task_progress', methods=['GET'])
@token_required
def get_task_progress():
    """
    Get all completed task indices for a given learning path.
    Query param: path_id=xxx
    Returns { completed_tasks: [{path_id, week_number, day_number, completed_tasks: [...]}] }
    """
    user_id = g.user['id']
    path_id = request.args.get('path_id')

    if not path_id:
        return jsonify({'error': 'path_id query parameter is required'}), 400

    # Try Supabase first
    if _supabase_available():
        try:
            supabase = current_app.supabase

            result = supabase.table('learning_progress').select('*').eq({
                'user_id': user_id,
                'path_id': path_id
            }).execute()

            if result.data:
                completed_tasks = []
                for record in result.data:
                    for task_idx in record.get('completed_tasks', []):
                        completed_tasks.append({
                            'week_number': record.get('week_number'),
                            'day_number': record.get('day_number'),
                            'task_index': task_idx
                        })

                return jsonify({
                    'status': 'ok',
                    'completed_tasks': completed_tasks
                })
        except Exception as e:
            logger.warning(f"Supabase query failed, using in-memory: {e}")

    # Check in-memory storage
    completed_tasks = []
    prefix = f"{user_id}:{path_id}"
    for key, tasks in _local_path_progress.items():
        if key.startswith(prefix):
            parts = key.split(':')
            week_num = int(parts[2]) if len(parts) > 2 else 0
            day_num = int(parts[3]) if len(parts) > 3 else 0
            for task_idx in tasks:
                completed_tasks.append({
                    'week_number': week_num,
                    'day_number': day_num,
                    'task_index': task_idx
                })

    return jsonify({
        'status': 'ok',
        'completed_tasks': completed_tasks
    })


# ── BUG 1 FIX: Role Chat route ─────────────────────────────────────────────
@dashboard.route('/role-chat', methods=['POST', 'OPTIONS'])
@token_required
def role_chat():
    """
    POST /api/role-chat
    Body: { role, messages, provider }
    Returns: { reply: "..." }
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    role = data.get('role', '')
    messages = data.get('messages', [])
    provider = data.get('provider', None)

    try:
        from .role_chat import generate_role_chat_reply
        reply = generate_role_chat_reply(role, messages, requested_provider=provider)
        return jsonify({'response': reply}), 200
    except Exception as e:
        logger.error(f'Role chat error: {e}')
        return jsonify({'error': 'AI chat is currently unavailable. Please try again.'}), 500


# ── BUG 2 FIX: GitHub Analysis route ───────────────────────────────────────
@dashboard.route('/analyze-github', methods=['POST', 'OPTIONS'])
def analyze_github():
    """
    POST /api/analyze-github
    Body: { github_username }
    Returns: GitHub analysis result dict
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body', 'available': False}), 400

    github_username = data.get('github_username', '').strip()
    if not github_username:
        return jsonify({'error': 'github_username is required', 'available': False}), 400

    try:
        from .github_analyzer import analyze_github_profile
        import os
        github_token = os.getenv('GITHUB_TOKEN')
        result = analyze_github_profile(github_username, github_token)

        if result.get('error'):
            return jsonify({**result, 'status': 'error', 'available': False}), 400

        return jsonify({**result, 'status': 'ok', 'available': True}), 200
    except Exception as e:
        logger.error(f'GitHub analysis error: {e}')
        return jsonify({'error': str(e), 'available': False}), 500
