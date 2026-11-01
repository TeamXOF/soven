# SOVEN API map

Generated from literal router prefixes and decorators. Check source models for exact schemas and middleware for access rules.

| Source | Method | Route | Handler |
|---|---|---|---|
| backend/routers/auth.py | POST | /api/auth/register | register |
| backend/routers/auth.py | POST | /api/auth/login | login |
| backend/routers/auth.py | POST | /api/auth/logout | logout |
| backend/routers/auth.py | GET | /api/auth/me | me |
| backend/routers/auth.py | POST | /api/auth/change-password | change_password |
| backend/routers/auth.py | GET | /api/auth/users | list_users |
| backend/routers/auth.py | POST | /api/auth/users/{user_id}/approve | approve_user |
| backend/routers/auth.py | POST | /api/auth/users/{user_id}/reject | reject_user |
| backend/routers/auth.py | DELETE | /api/auth/users/{user_id} | delete_user |
| backend/routers/pipeline.py | GET | /pipeline/sentences | generate_sentences |
| backend/routers/pipeline.py | POST | /pipeline/run | execute_pipeline |
| backend/routers/sessions.py | GET | /api/sessions/ | get_sessions |
| backend/routers/sessions.py | GET | /api/sessions/{session_id}/diagnosis | get_session_diagnosis |
| backend/routers/story_mode.py | GET | /api/v1/story/map | story_map |
| backend/routers/story_mode.py | GET | /api/v1/story/play | play_level |
| backend/routers/story_mode.py | POST | /api/v1/story/analyze | story_analyze |
| backend/routers/story_mode.py | POST | /api/v1/story/analyze-mock | story_analyze_mock |
| backend/routers/story_mode.py | GET | /api/v1/story/feedback/{attempt_id} | story_feedback |
| backend/routers/story_mode.py | GET | /api/v1/story/summary | story_summary |
| backend/routers/students.py | GET | /api/students/ | get_students |
| backend/routers/students.py | POST | /api/students/ | create_student |
| backend/routers/students.py | GET | /api/students/{student_id} | get_student |
| backend/routers/students.py | PUT | /api/students/{student_id} | update_student |
| backend/routers/students.py | DELETE | /api/students/{student_id} | delete_student |
| backend/routers/sync_ingest.py | POST | /api/v1/sync/ingest | ingest |
| backend/routers/teacher.py | GET | /api/v1/teacher/roster | teacher_roster |
| backend/routers/teacher.py | POST | /api/v1/teacher/students/{student_id}/parent-toggle | toggle_parent_updates |
| backend/routers/teacher.py | GET | /api/v1/students/{student_id}/parent-message | parent_message |
| backend/routers/teacher.py | GET | /api/v1/reports | reports |
| backend/routers/teacher.py | GET | /api/v1/practice/library | practice_library |
| backend/routers/teacher.py | GET | /api/v1/config/keys | get_keys |
| backend/routers/teacher.py | POST | /api/v1/config/keys | set_keys |
| backend/routers/v1.py | GET | /api/v1/activity | recorded_activity |
| backend/routers/v1.py | GET | /api/v1/health | v1_health |
| backend/routers/v1.py | GET | /api/v1/words/tip | word_tip |
| backend/routers/v1.py | GET | /api/v1/stories | list_stories |
| backend/routers/v1.py | GET | /api/v1/sessions | list_story_sessions |
| backend/routers/v1.py | POST | /api/v1/sessions | create_session |
| backend/routers/v1.py | POST | /api/v1/sessions/{session_id}/analyze | analyze_checkpoint |
| backend/routers/v1.py | POST | /api/v1/sessions/{session_id}/analyze-mock | analyze_checkpoint_mock |
| backend/routers/v1.py | GET | /api/v1/sessions/{session_id} | get_session |
| backend/routers/v1.py | GET | /api/v1/sessions/{session_id}/feedback/{checkpoint_id} | get_feedback |
| backend/routers/v1.py | GET | /api/v1/students/{student_id}/dashboard | student_dashboard |
| backend/routers/v1.py | GET | /api/v1/classroom/overview | classroom_overview |
| backend/routers/v1.py | POST | /api/v1/sync | trigger_sync |
| backend/routers/v1.py | GET | /api/v1/sync/status | sync_status |
| backend/routers/v1.py | WEBSOCKET | /ws/sessions/{session_id} | session_ws |
