"""Owner-only preferences and explicit completion, ready for the future UI."""
import json
from fastapi import APIRouter, HTTPException, Request, Response
from database.schema import get_db_connection
from core.reader_profiles import ProfileUpdate, create_profile, read_profile
from routers.auth import get_current_user

router = APIRouter(prefix='/api/auth', tags=['profiles'])


@router.get('/profile')
def profile(request: Request, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, 'Not logged in')
    with get_db_connection() as conn:
        return {'profile': read_profile(conn, user)}


@router.patch('/profile')
def update_profile(body: ProfileUpdate, request: Request, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, 'Not logged in')
    changes = body.model_dump(exclude_unset=True)
    with get_db_connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        current = read_profile(conn, user)
        if current['version'] != body.expected_version:
            raise HTTPException(409, 'Your profile changed. Reload it before saving again.')
        create_profile(conn, user['id'], current['reader_mode'], current['profile_completed'])
        mode = changes.get('persona_type') or changes.get('reader_mode')
        if mode:
            if mode not in ('child', 'adult', 'teacher', 'dyslexia'):
                raise HTTPException(422, 'Invalid persona type')
            current['reader_mode'] = mode
            conn.execute('UPDATE user_profiles SET reader_mode=? WHERE user_id=?', (mode, user['id']))
        for field in ('reading_language', 'interface_language'):
            if field in changes:
                if changes[field] is None:
                    raise HTTPException(422, f'{field} cannot be cleared')
                current[field] = changes[field]
        for field in ('native_language', 'translation_language'):
            if field in changes:
                current[field] = changes[field]
        if 'accessibility' in changes:
            if changes['accessibility'] is None:
                raise HTTPException(422, 'accessibility must be an object')
            current['accessibility'].update(changes['accessibility'])
        if 'native_language' in changes and current['native_language'] is None:
            current['profile_completed'] = False
        if body.complete_profile:
            if not current['native_language']:
                raise HTTPException(422, 'Choose your native language before completing your profile')
            current['profile_completed'] = True
        conn.execute('''UPDATE user_profiles SET reading_language=?, interface_language=?,
            native_language=?, translation_language=?, accessibility_json=?, profile_completed=?,
            version=version+1, updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND version=?''',
            (current['reading_language'], current['interface_language'], current['native_language'],
             current['translation_language'], json.dumps(current['accessibility']),
             int(current['profile_completed']), user['id'], body.expected_version))
        conn.commit()
        return {'profile': read_profile(conn, user)}
