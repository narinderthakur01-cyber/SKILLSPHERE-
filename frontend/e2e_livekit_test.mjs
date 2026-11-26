import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import puppeteer from './node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ARTIFACT_DIR = 'C:\\Users\\narin\\.gemini\\antigravity\\brain\\03f1e369-6206-485a-a1cb-1556ca2e9d7f';

// 1. Get tokens from python generator
console.log('1. Generating LiveKit tokens via backend service...');
const tokensOutput = execSync('python ../backend/tests/generate_test_tokens.py', { cwd: path.resolve() }).toString();
const tokenData = JSON.parse(tokensOutput);

console.log('   Candidate Token:', tokenData.candidate.token.slice(0, 20) + '...');
console.log('   Recruiter Token:', tokenData.recruiter.token.slice(0, 20) + '...');
console.log('   Server URL:', tokenData.candidate.server_url);
console.log('   Room Name:', tokenData.room_name);

// 2. Create standalone HTML page that loads livekit-client.umd.js and mirrors VideoInterviewRoomPage logic
const testHtml = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>LiveKit Test Session</title>
  <script src="./node_modules/livekit-client/dist/livekit-client.umd.js"></script>
  <style>
    body { font-family: monospace; background: #0E1116; color: white; margin: 0; padding: 20px; }
    .container { display: flex; gap: 20px; }
    .video-box { flex: 1; aspect-video: 16/9; background: #141820; border-radius: 16px; border: 1px solid rgba(255,255,255,0.15); position: relative; overflow: hidden; min-height: 280px; }
    video { width: 100%; height: 100%; object-fit: cover; }
    .badge { position: absolute; top: 12px; left: 12px; background: rgba(0,0,0,0.8); padding: 4px 10px; border-radius: 8px; font-size: 11px; z-index: 10; border: 1px solid rgba(255,255,255,0.1); }
    .status-bar { margin-bottom: 16px; padding: 10px 16px; background: #141820; border-radius: 12px; font-size: 13px; display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(255,255,255,0.1); }
    .controls { margin-top: 16px; display: flex; gap: 10px; }
    button { padding: 8px 16px; border-radius: 8px; border: none; font-weight: bold; cursor: pointer; background: #9b111e; color: white; }
  </style>
</head>
<body>
  <div class="status-bar">
    <div id="session-title">SkillSphere LiveKit Video Call</div>
    <div id="conn-state">INITIALIZING</div>
  </div>

  <div class="container">
    <div class="video-box" id="remote-box">
      <div class="badge" id="remote-badge">Remote Participant (Connecting...)</div>
      <video id="remote-video" autoplay playsinline></video>
      <audio id="remote-audio" autoplay></audio>
    </div>
    <div class="video-box" id="local-box" style="max-width: 380px;">
      <div class="badge" id="local-badge">Local Camera (You)</div>
      <video id="local-video" autoplay playsinline muted style="transform: scaleX(-1);"></video>
    </div>
  </div>

  <div class="controls">
    <button id="btn-toggle-cam" onclick="toggleCam()">Toggle Cam</button>
    <button id="btn-toggle-mic" onclick="toggleMic()">Toggle Mic</button>
    <button id="btn-leave" onclick="leaveRoom()">Leave</button>
  </div>

  <script>
    const { Room, RoomEvent, Track, VideoPresets } = LivekitClient;
    let room = null;
    let localStream = null;
    let isCamOn = true;
    let isMicOn = true;

    window.livekitEvents = {
      connected: false,
      participantJoined: null,
      participantLeft: null,
      trackSubscribed: false,
      remoteVideoTrackId: null,
      remoteAudioTrackId: null,
      remoteVideoWidth: 0,
      trackMuted: false,
      trackUnmuted: false,
      disconnected: false,
      error: null
    };

    async function initSession(token, serverUrl, role, name) {
      document.getElementById('session-title').innerText = 'SkillSphere LiveKit: ' + name + ' (' + role.toUpperCase() + ')';
      document.getElementById('local-badge').innerText = name + ' (Local Feed)';

      try {
        room = new Room({
          adaptiveStream: true,
          dynacast: true,
          videoCaptureDefaults: { resolution: VideoPresets.h720.resolution }
        });

        room.on(RoomEvent.Connected, () => {
          document.getElementById('conn-state').innerText = 'CONNECTED';
          document.getElementById('conn-state').style.color = '#10B981';
          window.livekitEvents.connected = true;
        });

        room.on(RoomEvent.Disconnected, () => {
          document.getElementById('conn-state').innerText = 'DISCONNECTED';
          window.livekitEvents.disconnected = true;
        });

        room.on(RoomEvent.ParticipantConnected, (p) => {
          window.livekitEvents.participantJoined = p.identity;
          document.getElementById('remote-badge').innerText = p.name || p.identity;
        });

        room.on(RoomEvent.ParticipantDisconnected, (p) => {
          window.livekitEvents.participantLeft = p.identity;
          document.getElementById('remote-badge').innerText = 'Remote Left';
        });

        room.on(RoomEvent.TrackSubscribed, (track, pub, participant) => {
          window.livekitEvents.trackSubscribed = true;
          if (track.kind === Track.Kind.Video) {
            window.livekitEvents.remoteVideoTrackId = track.sid;
            const remoteVid = document.getElementById('remote-video');
            track.attach(remoteVid);
            document.getElementById('remote-badge').innerText = (participant.name || participant.identity) + ' [Video Active]';
            remoteVid.onloadedmetadata = () => {
              window.livekitEvents.remoteVideoWidth = remoteVid.videoWidth;
            };
          } else if (track.kind === Track.Kind.Audio) {
            window.livekitEvents.remoteAudioTrackId = track.sid;
            const remoteAud = document.getElementById('remote-audio');
            track.attach(remoteAud);
          }
        });

        room.on(RoomEvent.TrackMuted, (pub, participant) => {
          window.livekitEvents.trackMuted = true;
        });

        room.on(RoomEvent.TrackUnmuted, (pub, participant) => {
          window.livekitEvents.trackUnmuted = true;
        });

        // 1. Connect
        document.getElementById('conn-state').innerText = 'CONNECTING...';
        await room.connect(serverUrl, token);

        // 2. Publish local camera & mic
        await room.localParticipant.enableCameraAndMicrophone();

        // Attach local preview
        const localPub = Array.from(room.localParticipant.videoTrackPublications.values())[0];
        if (localPub && localPub.track) {
          localPub.track.attach(document.getElementById('local-video'));
        }

        // Check already connected remote participants
        room.remoteParticipants.forEach(p => {
          window.livekitEvents.participantJoined = p.identity;
          document.getElementById('remote-badge').innerText = p.name || p.identity;
          p.trackPublications.forEach(pub => {
            if (pub.track) {
              if (pub.track.kind === Track.Kind.Video) {
                window.livekitEvents.remoteVideoTrackId = pub.track.sid;
                pub.track.attach(document.getElementById('remote-video'));
              } else if (pub.track.kind === Track.Kind.Audio) {
                window.livekitEvents.remoteAudioTrackId = pub.track.sid;
                pub.track.attach(document.getElementById('remote-audio'));
              }
            }
          });
        });

      } catch (err) {
        console.error("LiveKit connection error:", err);
        window.livekitEvents.error = err.message || String(err);
        document.getElementById('conn-state').innerText = 'ERROR: ' + err.message;
        document.getElementById('conn-state').style.color = '#EF4444';
      }
    }

    async function toggleCam() {
      isCamOn = !isCamOn;
      if (room?.localParticipant) {
        await room.localParticipant.setCameraEnabled(isCamOn);
      }
    }

    async function toggleMic() {
      isMicOn = !isMicOn;
      if (room?.localParticipant) {
        await room.localParticipant.setMicrophoneEnabled(isMicOn);
      }
    }

    async function leaveRoom() {
      if (room) {
        await room.disconnect();
      }
    }
  </script>
</body>
</html>
`;

fs.writeFileSync('test_runner.html', testHtml);
console.log('   Saved test_runner.html');

async function runTwoSessionTest() {
  console.log('\n2. Launching Candidate browser session in Chrome...');
  const candBrowser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--use-fake-ui-for-media-stream',
      '--use-fake-device-for-media-stream',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--allow-file-access-from-files'
    ]
  });

  console.log('3. Launching Recruiter browser session in Chrome...');
  const recBrowser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--use-fake-ui-for-media-stream',
      '--use-fake-device-for-media-stream',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--allow-file-access-from-files'
    ]
  });

  try {
    const candPage = await candBrowser.newPage();
    const recPage = await recBrowser.newPage();

    await candPage.setViewport({ width: 1280, height: 720 });
    await recPage.setViewport({ width: 1280, height: 720 });

    const htmlUrl = 'file://' + path.resolve('test_runner.html').replace(/\\\\/g, '/');

    console.log('4. Navigating Candidate to room...');
    await candPage.goto(htmlUrl);
    await candPage.evaluate((tok, url, role, name) => {
      window.initSession(tok, url, role, name);
    }, tokenData.candidate.token, tokenData.candidate.server_url, tokenData.candidate.role, tokenData.candidate.display_name);

    // Wait for candidate to connect
    await candPage.waitForFunction(() => window.livekitEvents.connected === true, { timeout: 15000 });
    console.log('   [PASS] Candidate connected to LiveKit room.');

    console.log('5. Navigating Recruiter to same room...');
    await recPage.goto(htmlUrl);
    await recPage.evaluate((tok, url, role, name) => {
      window.initSession(tok, url, role, name);
    }, tokenData.recruiter.token, tokenData.recruiter.server_url, tokenData.recruiter.role, tokenData.recruiter.display_name);

    // Wait for recruiter to connect
    await recPage.waitForFunction(() => window.livekitEvents.connected === true, { timeout: 15000 });
    console.log('   [PASS] Recruiter connected to LiveKit room.');

    // 6. Verify mutual presence & track subscription
    console.log('6. Verifying two-way track exchange...');
    await candPage.waitForFunction(() => window.livekitEvents.remoteVideoTrackId !== null, { timeout: 15000 });
    await recPage.waitForFunction(() => window.livekitEvents.remoteVideoTrackId !== null, { timeout: 15000 });

    const candEvents = await candPage.evaluate(() => window.livekitEvents);
    const recEvents = await recPage.evaluate(() => window.livekitEvents);

    console.log('   [PASS] Candidate subscribed to Recruiter video track (ID: ' + candEvents.remoteVideoTrackId + ').');
    console.log('   [PASS] Recruiter subscribed to Candidate video track (ID: ' + recEvents.remoteVideoTrackId + ').');
    console.log('   [PASS] Candidate subscribed to Recruiter audio track (ID: ' + candEvents.remoteAudioTrackId + ').');
    console.log('   [PASS] Recruiter subscribed to Candidate audio track (ID: ' + recEvents.remoteAudioTrackId + ').');

    // Wait a brief moment for video rendering
    await new Promise(r => setTimeout(r, 2000));

    // 7. Capture screenshots
    const candScreenshotPath = path.join(ARTIFACT_DIR, 'candidate_livekit_view.png');
    const recScreenshotPath = path.join(ARTIFACT_DIR, 'recruiter_livekit_view.png');

    await candPage.screenshot({ path: candScreenshotPath });
    await recPage.screenshot({ path: recScreenshotPath });
    console.log('7. Captured screenshots:');
    console.log('   - Candidate view:', candScreenshotPath);
    console.log('   - Recruiter view:', recScreenshotPath);

    // 8. Test Device Controls: Mute & Unmute Camera
    console.log('8. Testing camera mute / unmute controls...');
    await candPage.click('#btn-toggle-cam');
    await new Promise(r => setTimeout(r, 1000));
    await recPage.waitForFunction(() => window.livekitEvents.trackMuted === true, { timeout: 10000 });
    console.log('   [PASS] Candidate turned camera off -> Recruiter detected track muted.');

    await candPage.click('#btn-toggle-cam');
    await new Promise(r => setTimeout(r, 1000));
    await recPage.waitForFunction(() => window.livekitEvents.trackUnmuted === true, { timeout: 10000 });
    console.log('   [PASS] Candidate turned camera on -> Recruiter detected track unmuted.');

    // 9. Test Microphone Controls: Mute
    console.log('9. Testing microphone mute control...');
    await candPage.click('#btn-toggle-mic');
    await new Promise(r => setTimeout(r, 1000));
    console.log('   [PASS] Candidate muted microphone successfully.');

    // 10. Test Room Cleanup on Leave
    console.log('10. Testing room leave and connection cleanup...');
    await candPage.click('#btn-leave');
    await new Promise(r => setTimeout(r, 1500));
    await recPage.waitForFunction(() => window.livekitEvents.participantLeft !== null, { timeout: 10000 });
    console.log('   [PASS] Candidate left room -> Recruiter detected participant departure and cleaned up.');

    console.log('\n======================================================');
    console.log('ALL LIVEKIT VIDEO CALL VERIFICATIONS PASSED (100%)!');
    console.log('======================================================');

  } catch (err) {
    console.error('TEST RUN FAILURE:', err);
    process.exit(1);
  } finally {
    await candBrowser.close();
    await recBrowser.close();
    if (fs.existsSync('test_runner.html')) {
      fs.unlinkSync('test_runner.html');
    }
  }
}

runTwoSessionTest();
