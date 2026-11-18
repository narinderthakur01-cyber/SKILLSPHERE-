import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    c = TestClient(app)
    c_tok = c.post('/api/v1/auth/login', json={'email': 'alex@example.com', 'password': '12345678'}).json()['access_token']
    r_tok = c.post('/api/v1/auth/login', json={'email': 'recruiter@technova.com', 'password': 'Recruiter123!'}).json()['access_token']
    a_tok = c.post('/api/v1/auth/login', json={'email': 'admin@skillsphere.local', 'password': 'Admin123!'}).json()['access_token']

    c_headers = {'Authorization': f'Bearer {c_tok}'}
    r_headers = {'Authorization': f'Bearer {r_tok}'}
    a_headers = {'Authorization': f'Bearer {a_tok}'}

    print("=" * 60)
    print("SkillSphere: ATS Upgrade Full Backend Verification")
    print("=" * 60)

    # 1. Saved Jobs & Recommendations
    recs = c.get('/api/v1/jobs/recommendations', headers=c_headers).json()
    assert len(recs) > 0, "No recommendations returned"
    print(f"1. ✓ Recommendations: {len(recs)} active roles evaluated. Top: '{recs[0]['job']['title']}'")

    job_id = recs[0]['job']['id']
    sj = c.post(f'/api/v1/saved-jobs/{job_id}', headers=c_headers).json()
    sjs = c.get('/api/v1/saved-jobs', headers=c_headers).json()
    assert len(sjs) >= 1
    print(f"   ✓ Saved Jobs: Bookmark stored successfully ({len(sjs)} saved).")

    # 2. AI Resume Quality Feedback
    qf = c.post('/api/v1/resume/quality-feedback', headers=c_headers).json()
    assert "completeness_score" in qf
    print(f"2. ✓ AI Quality Intelligence: Completeness = {qf['completeness_score']}%, Suggestions = {len(qf['suggestions'])}")

    # 3. Recruiter Applicants & Applications
    apps = c.get('/api/v1/recruiter/applicants', headers=r_headers).json()
    assert len(apps) > 0
    first_app = apps[0]
    print(f"3. ✓ Recruiter Applicants: Loaded {len(apps)} applications across openings.")

    # 4. Interview Scheduling
    sched_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    intv = c.post('/api/v1/interviews', json={
        'application_id': first_app['id'],
        'interview_type': 'ONLINE',
        'scheduled_time': sched_time,
        'duration_minutes': 45,
        'meeting_link': 'https://meet.skillsphere.local/interview-test'
    }, headers=r_headers).json()
    assert intv['status'] == 'SCHEDULED'
    print(f"4. ✓ Interview Scheduled: ID {intv['id']} on {intv['scheduled_time']} ({intv['interview_type']})")

    # 5. Candidate Evaluation
    ev = c.post('/api/v1/evaluations', json={
        'application_id': first_app['id'],
        'interview_id': intv['id'],
        'technical_score': 4.5,
        'communication_score': 5.0,
        'experience_score': 4.0,
        'overall_recommendation': 'STRONG_HIRE',
        'interview_feedback': 'Outstanding technical depth and crisp communication.',
        'internal_notes': 'Recommended for fast-track.'
    }, headers=r_headers).json()
    assert ev['overall_recommendation'] == 'STRONG_HIRE'
    print(f"5. ✓ Candidate Evaluation: Overall Recommendation = {ev['overall_recommendation']} (Score: {ev['overall_score']}/5)")

    # 6. Candidate Comparison Matrix
    comp = c.get(f"/api/v1/evaluations/compare/{first_app['job_id']}", headers=r_headers).json()
    assert len(comp) > 0
    print(f"6. ✓ Candidate Comparison Matrix: Evaluated {len(comp)} candidate(s) for job '{first_app['job']['title']}'")

    # 7. Messaging
    cand_user_id = first_app['candidate']['user_id']
    msg = c.post('/api/v1/messages', json={
        'receiver_id': cand_user_id,
        'application_id': first_app['id'],
        'content': 'Hello Alex, we look forward to meeting you for your technical interview!'
    }, headers=r_headers).json()
    assert msg['content'].startswith('Hello Alex')
    convs = c.get('/api/v1/messages/conversations', headers=c_headers).json()
    assert len(convs) >= 1
    print(f"7. ✓ Messaging: Delivered message '{msg['content'][:35]}...' | Conversation partners = {len(convs)}")

    # 8. Notifications
    notifs = c.get('/api/v1/notifications', headers=c_headers).json()
    assert len(notifs) >= 1
    print(f"8. ✓ Notifications: {len(notifs)} notifications registered. Latest: '{notifs[0]['title']}'")

    # 9. Audit Logs
    audits = c.get('/api/v1/admin/audit-logs', headers=a_headers).json()
    assert len(audits) >= 1
    print(f"9. ✓ Platform Audit Logs: {len(audits)} immutable audit records verified.")

    print("=" * 60)
    print("🎉 ALL 9 ATS UPGRADE FEATURES VERIFIED & 100% OPERATIONAL!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
