import sys
import json
from pathlib import Path

# Add backend root to path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.services.livekit_service import LiveKitService

def main():
    room_name = "skillsphere-e2e-livekit-room"
    
    cand_token = LiveKitService.generate_room_token(
        room_name=room_name,
        user_id="candidate-alex-rivera-uuid",
        user_name="Alex Rivera",
        role="candidate"
    )
    
    rec_token = LiveKitService.generate_room_token(
        room_name=room_name,
        user_id="recruiter-sarah-jenkins-uuid",
        user_name="Sarah Jenkins",
        role="recruiter"
    )
    
    output = {
        "room_name": room_name,
        "candidate": cand_token,
        "recruiter": rec_token
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
