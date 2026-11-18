/**
 * SkillSphere Client-Side Privacy-First Face Presence Engine.
 * 
 * PRIVACY SPECIFICATION:
 * - Operates 100% locally in browser memory.
 * - Never captures, transmits, or saves video frames or images to any server, database, or disk.
 * - Only outputs high-level presence telemetry signals (count of faces detected: 0, 1, or >1).
 */

class FacePresenceDetector {
  constructor() {
    this.nativeDetector = null;
    this.canvas = null;
    this.ctx = null;
    this.initNativeDetector();
  }

  async initNativeDetector() {
    if (typeof window !== 'undefined' && 'FaceDetector' in window) {
      try {
        // Native Chromium Shape Detection API
        this.nativeDetector = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 4 });
      } catch (err) {
        this.nativeDetector = null;
      }
    }
  }

  getOffscreenCanvas(width = 120, height = 90) {
    if (!this.canvas) {
      this.canvas = document.createElement('canvas');
      this.canvas.width = width;
      this.canvas.height = height;
      this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
    }
    return { canvas: this.canvas, ctx: this.ctx };
  }

  /**
   * Evaluates face presence from a live HTMLVideoElement.
   * Returns:
   * {
   *   faceCount: number, // 0 = absent, 1 = normal, >1 = multiple faces
   *   status: 'VISIBLE' | 'ABSENT' | 'MULTIPLE',
   *   confidence: number
   * }
   */
  async detect(videoElement) {
    if (!videoElement || videoElement.readyState < 2 || videoElement.videoWidth === 0) {
      return { faceCount: 1, status: 'VISIBLE', confidence: 0.5 };
    }

    // Path 1: Native Chromium FaceDetector if supported
    if (this.nativeDetector) {
      try {
        const faces = await this.nativeDetector.detect(videoElement);
        const count = faces ? faces.length : 0;
        if (count === 0) {
          return { faceCount: 0, status: 'ABSENT', confidence: 0.9 };
        } else if (count > 1) {
          return { faceCount: count, status: 'MULTIPLE', confidence: 0.85 };
        }
        return { faceCount: 1, status: 'VISIBLE', confidence: 0.95 };
      } catch {
        // Fall back to Canvas heuristic
      }
    }

    // Path 2: Lightweight Canvas Skin-Color & Contrast Heuristic Detector
    try {
      const { canvas, ctx } = this.getOffscreenCanvas(120, 90);
      ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
      const frameData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = frameData.data;
      const totalPixels = canvas.width * canvas.height;

      let skinPixels = 0;
      let leftClusterSkin = 0;
      let rightClusterSkin = 0;
      let totalLuminance = 0;
      const halfWidth = canvas.width / 2;

      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];

        // Perceived luminance
        const lum = 0.299 * r + 0.587 * g + 0.114 * b;
        totalLuminance += lum;

        // Standard biometric human skin-tone detection in RGB space:
        // (R > 95) & (G > 40) & (B > 20) & (max-min > 15) & (|R-G| > 15) & (R > G) & (R > B)
        const maxVal = Math.max(r, g, b);
        const minVal = Math.min(r, g, b);
        const isSkin = (
          r > 70 && g > 35 && b > 20 &&
          (maxVal - minVal) > 12 &&
          Math.abs(r - g) > 10 &&
          r > g && r > b
        );

        if (isSkin) {
          skinPixels++;
          const pixelIndex = i / 4;
          const x = pixelIndex % canvas.width;
          if (x < halfWidth * 0.85) {
            leftClusterSkin++;
          } else if (x > halfWidth * 1.15) {
            rightClusterSkin++;
          }
        }
      }

      const avgLuminance = totalLuminance / totalPixels;
      const skinCoverage = skinPixels / totalPixels;

      // Dark screen, camera covered or empty frame
      if (avgLuminance < 15 || skinCoverage < 0.05) {
        return {
          faceCount: 0,
          status: 'ABSENT',
          confidence: Math.round((1 - skinCoverage) * 100) / 100
        };
      }

      // Check for two separate distinct people in frame (both left and right halves have significant independent coverage)
      const leftCoverage = leftClusterSkin / (totalPixels / 2);
      const rightCoverage = rightClusterSkin / (totalPixels / 2);

      if (leftCoverage > 0.16 && rightCoverage > 0.16) {
        return {
          faceCount: 2,
          status: 'MULTIPLE',
          confidence: 0.82
        };
      }

      return {
        faceCount: 1,
        status: 'VISIBLE',
        confidence: Math.min(0.98, Math.max(0.65, skinCoverage * 3))
      };
    } catch (e) {
      // In case of canvas read error, maintain benign visible state
      return { faceCount: 1, status: 'VISIBLE', confidence: 0.6 };
    }
  }
}

export const faceDetector = new FacePresenceDetector();
