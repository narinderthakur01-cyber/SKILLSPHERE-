import os
import json
import logging
import uuid
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.core.config import settings

logger = logging.getLogger("skillsphere.email")

# In-memory test store for mock deliveries during automated tests
_mock_email_deliveries: List[Dict[str, Any]] = []

def get_mock_deliveries() -> List[Dict[str, Any]]:
    """Retrieve recorded mock emails for assertions during testing."""
    return list(_mock_email_deliveries)

def clear_mock_deliveries() -> None:
    """Clear recorded mock emails between test runs."""
    _mock_email_deliveries.clear()

def _wrap_email_template(title: str, preheader: str, body_content: str) -> str:
    """Wraps body content in the canonical SkillSphere Charcoal × Oxblood responsive email shell."""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #1B1A1B; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #EFE9E3;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #1B1A1B; padding: 40px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 580px; background-color: #242023; border: 1px solid rgba(197, 164, 155, 0.2); border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
          <!-- Header Branding -->
          <tr>
            <td style="padding: 32px 36px; background-color: #1F1B1E; border-bottom: 1px solid rgba(197, 164, 155, 0.15); text-align: left;">
              <table role="presentation" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="background-color: #914F51; color: #EFE9E3; font-weight: 800; font-size: 16px; width: 36px; height: 36px; text-align: center; border-radius: 10px;">
                    S
                  </td>
                  <td style="padding-left: 12px; font-size: 20px; font-weight: 800; letter-spacing: -0.5px; color: #EFE9E3;">
                    SkillSphere
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Content -->
          <tr>
            <td style="padding: 36px; text-align: left;">
              <p style="margin: 0 0 12px 0; font-size: 12px; font-weight: 700; color: #C5A49B; text-transform: uppercase; letter-spacing: 1px;">
                {preheader}
              </p>
              {body_content}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 36px; background-color: #1B1A1B; border-top: 1px solid rgba(197, 164, 155, 0.1); text-align: center;">
              <p style="margin: 0 0 8px 0; font-size: 11px; color: rgba(197, 164, 155, 0.5);">
                &copy; 2026 SkillSphere Platform. Enterprise Applicant Tracking & AI Talent Intelligence.
              </p>
              <p style="margin: 0; font-size: 10px; color: rgba(197, 164, 155, 0.35);">
                This is an automated operational notification regarding your SkillSphere account security and authentication.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

class EmailService:
    @staticmethod
    def is_configured() -> bool:
        """Check if Brevo API credentials and sender email are configured."""
        return bool(settings.BREVO_API_KEY and settings.BREVO_API_KEY.strip() and settings.BREVO_SENDER_EMAIL and settings.BREVO_SENDER_EMAIL.strip())

    @classmethod
    def _dispatch_brevo_email(
        cls,
        subject: str,
        to_email: str,
        user_name: str,
        html_content: str,
        email_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Internal central dispatcher for Brevo Transactional Email API (https://api.brevo.com/v3/smtp/email).
        Handles configuration checks, mock recording for test environments, network communication,
        and safe diagnostic logging without leaking secrets.
        """
        # 1. Check if Brevo is configured in backend/.env
        if not cls.is_configured():
            print(
                f"[EMAIL SERVICE] WARNING: Brevo credentials missing in backend/.env "
                f"(BREVO_API_KEY_SET={bool(settings.BREVO_API_KEY)}, BREVO_SENDER_EMAIL_SET={bool(settings.BREVO_SENDER_EMAIL)}). "
                f"Email of type '{email_type}' NOT dispatched.",
                flush=True
            )
            return {
                "status": "unconfigured",
                "mode": "unconfigured",
                "delivered": False,
                "email_type": email_type,
                "detail": "BREVO_API_KEY or BREVO_SENDER_EMAIL is not configured in backend/.env"
            }

        # 2. Check if running in automated test mode
        is_test_env = getattr(settings, "TESTING", False) or os.environ.get("TESTING", "").lower() in ("true", "1", "yes") or force_mock
        if is_test_env:
            mock_entry = {
                "to_email": to_email,
                "user_name": user_name,
                "subject": subject,
                "email_type": email_type,
                "metadata": metadata or {},
                "mocked": True,
                "brevo_configured": True
            }
            _mock_email_deliveries.append(mock_entry)
            print(f"[EMAIL SERVICE] Automated test mode active: recorded mock email '{email_type}' for {to_email}", flush=True)
            mock_msg_id = f"mock-msg-{uuid.uuid4().hex[:12]}"
            return {
                "status": "delivered",
                "mode": "mock",
                "delivered": True,
                "message_id": mock_msg_id,
                "email_type": email_type,
                "detail": "Automated test mode; mock email recorded"
            }

        # 3. Live Brevo Transactional Email API Dispatch
        api_url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": settings.BREVO_API_KEY.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        sender_email = settings.BREVO_SENDER_EMAIL.strip()
        sender_name = settings.BREVO_SENDER_NAME or "SkillSphere"

        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": to_email.strip(),
                    "name": user_name or "SkillSphere User"
                }
            ],
            "subject": subject,
            "htmlContent": html_content
        }

        print(f"[EMAIL SERVICE] Initiating Brevo transactional dispatch ({email_type}) to: {to_email.strip()}", flush=True)
        print(f"[EMAIL SERVICE] Configured Sender: {sender_name} <{sender_email}>", flush=True)

        try:
            req = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                resp_data = resp.read().decode("utf-8")
                status_code = resp.status
                print(f"[EMAIL SERVICE] SUCCESS: Brevo API responded with HTTP {status_code}.", flush=True)
                msg_id = "N/A"
                try:
                    parsed_resp = json.loads(resp_data)
                    msg_id = parsed_resp.get("messageId", "N/A")
                    print(f"[EMAIL SERVICE] Brevo Message ID: {msg_id}", flush=True)
                except Exception:
                    pass
                return {
                    "status": "success",
                    "mode": "live",
                    "delivered": True,
                    "http_code": status_code,
                    "message_id": msg_id,
                    "email_type": email_type
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"[EMAIL SERVICE] ERROR: Brevo API rejected request with HTTP {e.code}: {err_body}", flush=True)
            return {
                "status": "error",
                "mode": "live",
                "delivered": False,
                "code": e.code,
                "email_type": email_type,
                "detail": err_body
            }
        except Exception as e:
            print(f"[EMAIL SERVICE] ERROR: Network/connection error communicating with Brevo: {str(e)}", flush=True)
            return {
                "status": "error",
                "mode": "live",
                "delivered": False,
                "email_type": email_type,
                "detail": str(e)
            }

    @classmethod
    def send_verification_email(
        cls,
        to_email: str,
        user_name: str,
        verification_token: str,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch an email verification link to a newly registered Candidate or Recruiter.
        """
        verify_link = f"{settings.FRONTEND_BASE_URL}/verify-email?token={verification_token}"
        expire_minutes = settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
        subject = "Verify Your SkillSphere Email Address"

        body = f"""
        <h1 style="margin: 0 0 18px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
          Confirm Your Email Address
        </h1>
        <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Welcome to SkillSphere, {user_name or 'there'}!<br>
          Thank you for joining our talent and recruitment ecosystem. To activate your account and access your dashboard, please verify your email address ({to_email}).
        </p>

        <!-- Verify Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 28px 0;">
          <tr>
            <td align="center" style="border-radius: 12px; background-color: #914F51;">
              <a href="{verify_link}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 13px; font-weight: 700; color: #EFE9E3; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 12px; border: 1px solid #C5A49B;">
                Verify Email Address &rarr;
              </a>
            </td>
          </tr>
        </table>

        <!-- Link fallback -->
        <p style="margin: 0 0 24px 0; font-size: 11px; line-height: 1.6; color: rgba(239, 233, 227, 0.6);">
          Button not working? Copy and paste this URL into your browser:<br>
          <a href="{verify_link}" style="color: #C5A49B; word-break: break-all;">{verify_link}</a>
        </p>

        <!-- Expiration Alert -->
        <div style="background-color: rgba(55, 48, 52, 0.6); border: 1px solid rgba(197, 164, 155, 0.2); border-radius: 12px; padding: 16px; margin: 24px 0;">
          <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #EFE9E3;">
            &#9201; <strong>Notice:</strong> This verification token expires in <strong>{expire_minutes} minutes</strong> and can only be used once.
          </p>
        </div>

        <p style="margin: 0; font-size: 12px; line-height: 1.6; color: rgba(197, 164, 155, 0.8);">
          If you did not create a SkillSphere account, no further action is required. This unverified record will automatically expire.
        </p>
        """

        html_content = _wrap_email_template("Verify Your SkillSphere Email Address", "Account Activation", body)
        return cls._dispatch_brevo_email(
            subject=subject,
            to_email=to_email,
            user_name=user_name,
            html_content=html_content,
            email_type="EMAIL_VERIFICATION",
            metadata={"verification_token": verification_token, "verify_link": verify_link},
            force_mock=force_mock
        )

    @classmethod
    def send_welcome_email(
        cls,
        to_email: str,
        user_name: str,
        role: str,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch a celebratory Welcome Email immediately following successful email verification.
        """
        role_label = "Recruiter & Talent Partner" if role == "RECRUITER" else "Professional Job Seeker"
        dashboard_link = f"{settings.FRONTEND_BASE_URL}/auth?mode=login"
        subject = "Welcome to SkillSphere — Your Account Is Verified"

        body = f"""
        <h1 style="margin: 0 0 18px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
          Welcome Aboard, {user_name or 'there'}!
        </h1>
        <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Your email address ({to_email}) has been successfully confirmed. Your SkillSphere account is now fully active with <strong>{role_label}</strong> privileges.
        </p>

        <div style="background-color: rgba(55, 48, 52, 0.6); border: 1px solid rgba(197, 164, 155, 0.2); border-radius: 12px; padding: 20px; margin: 24px 0;">
          <p style="margin: 0 0 10px 0; font-size: 13px; font-weight: 700; color: #EFE9E3;">What you can do next:</p>
          <ul style="margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.7; color: #C5A49B;">
            {"<li>Publish high-impact job postings and define customized assessments.</li><li>Shortlist applicants and track hiring funnel analytics.</li><li>Manage candidate practice rounds and evaluate submissions.</li>" if role == "RECRUITER" else "<li>Upload your resume for instant AI-powered OCR parsing and skill extraction.</li><li>Take technical practice assessments to test your problem-solving speed.</li><li>Apply for top positions and track live recruitment pipeline milestones.</li>"}
          </ul>
        </div>

        <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 28px 0;">
          <tr>
            <td align="center" style="border-radius: 12px; background-color: #914F51;">
              <a href="{dashboard_link}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 13px; font-weight: 700; color: #EFE9E3; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 12px; border: 1px solid #C5A49B;">
                Sign In To Your Workspace &rarr;
              </a>
            </td>
          </tr>
        </table>
        """

        html_content = _wrap_email_template("Welcome to SkillSphere", "Account Verified", body)
        return cls._dispatch_brevo_email(
            subject=subject,
            to_email=to_email,
            user_name=user_name,
            html_content=html_content,
            email_type="WELCOME_EMAIL",
            metadata={"role": role},
            force_mock=force_mock
        )

    @classmethod
    def send_security_alert_email(
        cls,
        to_email: str,
        user_name: str,
        event_title: str,
        event_description: str,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch a high-priority account security notification.
        """
        subject = f"SkillSphere — Security Alert: {event_title}"

        body = f"""
        <h1 style="margin: 0 0 18px 0; font-size: 22px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
          Security Alert: {event_title}
        </h1>
        <p style="margin: 0 0 18px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Hello {user_name or 'there'},<br>
          We observed the following account activity on your SkillSphere account ({to_email}):
        </p>

        <div style="background-color: rgba(55, 48, 52, 0.6); border: 1px solid rgba(197, 164, 155, 0.2); border-radius: 12px; padding: 18px; margin: 20px 0;">
          <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #EFE9E3;">
            {event_description}
          </p>
        </div>

        <p style="margin: 0; font-size: 12px; line-height: 1.6; color: rgba(197, 164, 155, 0.8);">
          If you performed this action, no further steps are needed. If you did NOT authorize this change, please sign in immediately and update your password, or contact security support.
        </p>
        """

        html_content = _wrap_email_template(f"Security Alert — {event_title}", "Security Notification", body)
        return cls._dispatch_brevo_email(
            subject=subject,
            to_email=to_email,
            user_name=user_name,
            html_content=html_content,
            email_type="SECURITY_ALERT",
            metadata={"event_title": event_title},
            force_mock=force_mock
        )

    @classmethod
    def send_password_reset_email(
        cls,
        to_email: str,
        user_name: str,
        reset_token: str,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch a branded password reset email via Brevo Transactional Email API.
        """
        reset_link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={reset_token}"
        expire_minutes = settings.PASSWORD_RESET_EXPIRE_MINUTES
        subject = "SkillSphere — Reset Your Password"

        body = f"""
        <h1 style="margin: 0 0 18px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
          Password Recovery Request
        </h1>
        <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Hello {user_name or 'there'},<br>
          We received an authentication reset request for your SkillSphere account ({to_email}). Click the secure button below to set a new password.
        </p>

        <!-- Reset Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 28px 0;">
          <tr>
            <td align="center" style="border-radius: 12px; background-color: #914F51;">
              <a href="{reset_link}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 13px; font-weight: 700; color: #EFE9E3; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 12px; border: 1px solid #C5A49B;">
                Reset Access Password &rarr;
              </a>
            </td>
          </tr>
        </table>

        <!-- Link fallback -->
        <p style="margin: 0 0 24px 0; font-size: 11px; line-height: 1.6; color: rgba(239, 233, 227, 0.6);">
          Button not working? Copy and paste this URL into your browser:<br>
          <a href="{reset_link}" style="color: #C5A49B; word-break: break-all;">{reset_link}</a>
        </p>

        <!-- Expiration Alert -->
        <div style="background-color: rgba(55, 48, 52, 0.6); border: 1px solid rgba(197, 164, 155, 0.2); border-radius: 12px; padding: 16px; margin: 24px 0;">
          <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #EFE9E3;">
            &#9201; <strong>Notice:</strong> This secure token expires in <strong>{expire_minutes} minutes</strong> and is strictly single-use.
          </p>
        </div>

        <!-- Security Warning -->
        <p style="margin: 0; font-size: 12px; line-height: 1.6; color: rgba(197, 164, 155, 0.8);">
          If you did not initiate this request, you can safely ignore this email. Your current password remains secure, and no changes have been applied to your account.
        </p>
        """

        html_content = _wrap_email_template("SkillSphere Password Reset", "Security Credential Reset", body)
        return cls._dispatch_brevo_email(
            subject=subject,
            to_email=to_email,
            user_name=user_name,
            html_content=html_content,
            email_type="PASSWORD_RESET",
            metadata={"reset_token": reset_token, "reset_link": reset_link},
            force_mock=force_mock
        )

    @classmethod
    def send_shortlisting_email(
        cls,
        to_email: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        assessment_info: Optional[Dict[str, Any]] = None,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch an official shortlisting notification to candidate via Brevo Transactional Email API.
        Conditionally includes First-Round Assessment details if an assessment has been assigned.
        """
        subject = "Congratulations! You Have Been Shortlisted — SkillSphere"
        dashboard_link = f"{settings.FRONTEND_BASE_URL}/dashboard?tab={'assessments' if assessment_info else 'applications'}"

        assessment_block = ""
        if assessment_info:
            deadline_str = assessment_info.get("deadline_at")
            if not deadline_str:
                deadline_display = "Please complete as soon as possible"
            elif isinstance(deadline_str, str):
                deadline_display = deadline_str
            else:
                try:
                    deadline_display = deadline_str.strftime("%B %d, %Y at %I:%M %p UTC")
                except Exception:
                    deadline_display = str(deadline_str)

            assessment_block = f"""
            <div style="background-color: rgba(55, 48, 52, 0.6); border: 1px solid rgba(197, 164, 155, 0.25); border-radius: 14px; padding: 22px; margin: 24px 0;">
              <p style="margin: 0 0 14px 0; font-size: 11px; font-weight: 800; color: #C5A49B; text-transform: uppercase; letter-spacing: 1px;">
                &#9889; First-Round Assessment Assigned
              </p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="4" style="font-size: 13px; line-height: 1.6; color: #EFE9E3;">
                <tr>
                  <td style="width: 120px; color: #C5A49B; font-weight: 600;">Assessment:</td>
                  <td style="font-weight: 700; color: #EFE9E3;">{assessment_info.get('title', 'Technical Assessment')}</td>
                </tr>
                <tr>
                  <td style="color: #C5A49B; font-weight: 600;">Duration:</td>
                  <td>{assessment_info.get('duration_minutes', 30)} Minutes</td>
                </tr>
                <tr>
                  <td style="color: #C5A49B; font-weight: 600;">Deadline:</td>
                  <td>{deadline_display}</td>
                </tr>
              </table>
              <p style="margin: 14px 0 0 0; font-size: 11px; color: rgba(197, 164, 155, 0.7); line-height: 1.5;">
                &bull; Assessments are strictly time-bound and enforce a single attempt policy.<br>
                &bull; Browser-based face presence monitoring and tab-switch supervision will be active during testing.
              </p>
            </div>
            """

        body = f"""
        <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
          Application Shortlisted!
        </h1>
        <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Hello <strong style="color: #EFE9E3;">{candidate_name or 'Candidate'}</strong>,
        </p>
        <p style="margin: 0 0 18px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Congratulations! Your application for <strong style="color: #EFE9E3;">{job_title}</strong> at <strong style="color: #EFE9E3;">{company_name}</strong> has been shortlisted by the recruiting team.
        </p>

        {assessment_block}

        <!-- Dashboard Action Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 26px 0;">
          <tr>
            <td align="center" style="border-radius: 12px; background-color: #914F51;">
              <a href="{dashboard_link}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 13px; font-weight: 700; color: #EFE9E3; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 12px; border: 1px solid #C5A49B;">
                {'View Assessment & Details' if assessment_info else 'Go To Candidate Dashboard'} &rarr;
              </a>
            </td>
          </tr>
        </table>

        <!-- Next Steps Box -->
        <div style="background-color: rgba(36, 32, 35, 0.5); border: 1px solid rgba(197, 164, 155, 0.15); border-radius: 12px; padding: 18px; margin: 24px 0;">
          <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 700; color: #EFE9E3; text-transform: uppercase; letter-spacing: 0.5px;">Next Steps</p>
          <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
            Please sign in to your SkillSphere Candidate Dashboard to view details and proceed with the recruitment process.
          </p>
        </div>

        <p style="margin: 24px 0 0 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
          Best regards,<br>
          <strong style="color: #EFE9E3;">The {company_name} Hiring Team & SkillSphere</strong>
        </p>
        """

        html_content = _wrap_email_template("Application Shortlisted — SkillSphere", "Recruitment Milestone", body)
        return cls._dispatch_brevo_email(
            subject=subject,
            to_email=to_email,
            user_name=candidate_name,
            html_content=html_content,
            email_type="SHORTLISTED",
            metadata={
                "job_title": job_title,
                "company_name": company_name,
                "has_assessment": bool(assessment_info)
            },
            force_mock=force_mock
        )

    @classmethod
    def send_interview_invitation_email(
        cls,
        to_email: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        interview_type: str,
        scheduled_time: datetime,
        duration_minutes: int,
        meeting_link: Optional[str] = None,
        location: Optional[str] = None,
        instructions: Optional[str] = None,
        recruiter_name: Optional[str] = None,
        recruiter_email: Optional[str] = None,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch an official interview invitation email via Brevo Transactional Email API.
        """
        subject = f"Interview Invitation — {job_title} | SkillSphere"
        dashboard_link = f"{settings.FRONTEND_BASE_URL}/dashboard?tab=interviews"

        time_display = scheduled_time.strftime("%A, %B %d, %Y at %I:%M %p UTC") if isinstance(scheduled_time, datetime) else str(scheduled_time)
        mode_label = interview_type.upper().replace("_", " ")

        location_row = ""
        if interview_type.upper() == "ONLINE" and meeting_link:
            location_row = f"""
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Meeting Link:</td>
              <td style="padding: 6px 0;"><a href="{meeting_link}" target="_blank" style="color: #EFE9E3; word-break: break-all; font-weight: 700; text-decoration: underline;">Join Interview Meeting</a></td>
            </tr>
            """
        elif location:
            location_row = f"""
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Location:</td>
              <td style="padding: 6px 0; color: #EFE9E3;">{location}</td>
            </tr>
            """

        instructions_block = ""
        if instructions and instructions.strip():
            instructions_block = f"""
            <div style="background-color: rgba(55, 48, 52, 0.4); border-left: 3px solid #914F51; border-radius: 4px; padding: 14px 18px; margin: 20px 0;">
              <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 800; color: #C5A49B; text-transform: uppercase; letter-spacing: 0.5px;">Candidate Instructions:</p>
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #EFE9E3;">{instructions.strip()}</p>
            </div>
            """

        recruiter_block = ""
        if recruiter_name or recruiter_email:
            r_info = f"{recruiter_name} ({recruiter_email})" if (recruiter_name and recruiter_email) else (recruiter_name or recruiter_email)
            recruiter_block = f"""
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Recruiter:</td>
              <td style="padding: 6px 0; color: #EFE9E3;">{r_info}</td>
            </tr>
            """

        body = f"""
        <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
          Interview Invitation
        </h1>
        <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Hello <strong style="color: #EFE9E3;">{candidate_name or 'Candidate'}</strong>,
        </p>
        <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          You have been selected for an interview for the <strong style="color: #EFE9E3;">{job_title}</strong> role at <strong style="color: #EFE9E3;">{company_name}</strong>. Here are the confirmed schedule details:
        </p>

        <!-- Interview Details Card -->
        <div style="background-color: rgba(55, 48, 52, 0.6); border: 1px solid rgba(197, 164, 155, 0.25); border-radius: 14px; padding: 22px; margin: 24px 0;">
          <p style="margin: 0 0 16px 0; font-size: 11px; font-weight: 800; color: #C5A49B; text-transform: uppercase; letter-spacing: 1px;">
            &#128197; Interview Schedule & Logistics
          </p>
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="font-size: 13px; line-height: 1.6; color: #EFE9E3;">
            <tr>
              <td style="width: 130px; color: #C5A49B; font-weight: 600; padding: 6px 0;">Position:</td>
              <td style="padding: 6px 0; font-weight: 700; color: #EFE9E3;">{job_title}</td>
            </tr>
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Company:</td>
              <td style="padding: 6px 0; color: #EFE9E3;">{company_name}</td>
            </tr>
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Date & Time:</td>
              <td style="padding: 6px 0; font-weight: 700; color: #EFE9E3;">{time_display}</td>
            </tr>
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Estimated Duration:</td>
              <td style="padding: 6px 0; color: #EFE9E3;">{duration_minutes} Minutes</td>
            </tr>
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Interview Mode:</td>
              <td style="padding: 6px 0; color: #EFE9E3; font-weight: 700;">{mode_label}</td>
            </tr>
            {location_row}
            {recruiter_block}
          </table>

          {instructions_block}
        </div>

        <!-- Dashboard Action Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 26px 0;">
          <tr>
            <td align="center" style="border-radius: 12px; background-color: #914F51;">
              <a href="{dashboard_link}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 13px; font-weight: 700; color: #EFE9E3; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 12px; border: 1px solid #C5A49B;">
                View In Candidate Dashboard &rarr;
              </a>
            </td>
          </tr>
        </table>

        <div style="background-color: rgba(36, 32, 35, 0.5); border: 1px solid rgba(197, 164, 155, 0.15); border-radius: 12px; padding: 16px; margin: 24px 0;">
          <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #C5A49B;">
            &#128161; <strong>Preparation Tip:</strong> Test your microphone and camera beforehand. Be ready 5 minutes before your scheduled start time.
          </p>
        </div>

        <p style="margin: 24px 0 0 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
          Warm regards,<br>
          <strong style="color: #EFE9E3;">The {company_name} Talent Team & SkillSphere</strong>
        </p>
        """

        html_content = _wrap_email_template(f"Interview Invitation — {job_title}", "Interview Scheduled", body)
        return cls._dispatch_brevo_email(
            subject=subject,
            to_email=to_email,
            user_name=candidate_name,
            html_content=html_content,
            email_type="INTERVIEW_INVITATION",
            metadata={
                "job_title": job_title,
                "company_name": company_name,
                "scheduled_time": str(scheduled_time),
                "interview_type": interview_type
            },
            force_mock=force_mock
        )

    @classmethod
    def send_interview_update_email(
        cls,
        to_email: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        interview_type: str,
        scheduled_time: datetime,
        duration_minutes: int,
        meeting_link: Optional[str] = None,
        location: Optional[str] = None,
        instructions: Optional[str] = None,
        recruiter_name: Optional[str] = None,
        recruiter_email: Optional[str] = None,
        changes_summary: Optional[str] = None,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch an interview rescheduling/update notification via Brevo Transactional Email API.
        """
        subject = f"Interview Rescheduled — {job_title} | SkillSphere"
        dashboard_link = f"{settings.FRONTEND_BASE_URL}/dashboard?tab=interviews"

        time_display = scheduled_time.strftime("%A, %B %d, %Y at %I:%M %p UTC") if isinstance(scheduled_time, datetime) else str(scheduled_time)
        mode_label = interview_type.upper().replace("_", " ")

        location_row = ""
        if interview_type.upper() == "ONLINE" and meeting_link:
            location_row = f"""
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Meeting Link:</td>
              <td style="padding: 6px 0;"><a href="{meeting_link}" target="_blank" style="color: #EFE9E3; word-break: break-all; font-weight: 700; text-decoration: underline;">Join Interview Meeting</a></td>
            </tr>
            """
        elif location:
            location_row = f"""
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Location:</td>
              <td style="padding: 6px 0; color: #EFE9E3;">{location}</td>
            </tr>
            """

        instructions_block = ""
        if instructions and instructions.strip():
            instructions_block = f"""
            <div style="background-color: rgba(55, 48, 52, 0.4); border-left: 3px solid #914F51; border-radius: 4px; padding: 14px 18px; margin: 20px 0;">
              <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 800; color: #C5A49B; text-transform: uppercase; letter-spacing: 0.5px;">Updated Instructions:</p>
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #EFE9E3;">{instructions.strip()}</p>
            </div>
            """

        summary_block = ""
        if changes_summary:
            summary_block = f"""
            <div style="background-color: rgba(145, 79, 81, 0.2); border: 1px solid rgba(145, 79, 81, 0.4); border-radius: 10px; padding: 14px 18px; margin: 18px 0;">
              <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #EFE9E3;">
                <strong>Notice:</strong> {changes_summary}
              </p>
            </div>
            """

        body = f"""
        <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
          Interview Rescheduled
        </h1>
        <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Hello <strong style="color: #EFE9E3;">{candidate_name or 'Candidate'}</strong>,
        </p>
        <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Your interview for the <strong style="color: #EFE9E3;">{job_title}</strong> role at <strong style="color: #EFE9E3;">{company_name}</strong> has been updated. Please review the updated schedule details below:
        </p>

        {summary_block}

        <div style="background-color: rgba(55, 48, 52, 0.6); border: 1px solid rgba(197, 164, 155, 0.25); border-radius: 14px; padding: 22px; margin: 24px 0;">
          <p style="margin: 0 0 16px 0; font-size: 11px; font-weight: 800; color: #C5A49B; text-transform: uppercase; letter-spacing: 1px;">
            &#128197; Updated Interview Schedule
          </p>
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="font-size: 13px; line-height: 1.6; color: #EFE9E3;">
            <tr>
              <td style="width: 130px; color: #C5A49B; font-weight: 600; padding: 6px 0;">Position:</td>
              <td style="padding: 6px 0; font-weight: 700; color: #EFE9E3;">{job_title}</td>
            </tr>
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">New Date & Time:</td>
              <td style="padding: 6px 0; font-weight: 700; color: #EFE9E3;">{time_display}</td>
            </tr>
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Estimated Duration:</td>
              <td style="padding: 6px 0; color: #EFE9E3;">{duration_minutes} Minutes</td>
            </tr>
            <tr>
              <td style="color: #C5A49B; font-weight: 600; padding: 6px 0;">Interview Mode:</td>
              <td style="padding: 6px 0; color: #EFE9E3; font-weight: 700;">{mode_label}</td>
            </tr>
            {location_row}
          </table>

          {instructions_block}
        </div>

        <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 26px 0;">
          <tr>
            <td align="center" style="border-radius: 12px; background-color: #914F51;">
              <a href="{dashboard_link}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 13px; font-weight: 700; color: #EFE9E3; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 12px; border: 1px solid #C5A49B;">
                Confirm In Dashboard &rarr;
              </a>
            </td>
          </tr>
        </table>

        <p style="margin: 24px 0 0 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
          Best regards,<br>
          <strong style="color: #EFE9E3;">The {company_name} Talent Team & SkillSphere</strong>
        </p>
        """

        html_content = _wrap_email_template(f"Interview Rescheduled — {job_title}", "Interview Update", body)
        return cls._dispatch_brevo_email(
            subject=subject,
            to_email=to_email,
            user_name=candidate_name,
            html_content=html_content,
            email_type="INTERVIEW_RESCHEDULED",
            metadata={
                "job_title": job_title,
                "company_name": company_name,
                "scheduled_time": str(scheduled_time),
                "interview_type": interview_type
            },
            force_mock=force_mock
        )

    @classmethod
    def send_interview_cancellation_email(
        cls,
        to_email: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        scheduled_time: datetime,
        recruiter_name: Optional[str] = None,
        reason: Optional[str] = None,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch an interview cancellation notification via Brevo Transactional Email API.
        """
        subject = f"Interview Cancelled — {job_title} | SkillSphere"
        time_display = scheduled_time.strftime("%A, %B %d, %Y at %I:%M %p UTC") if isinstance(scheduled_time, datetime) else str(scheduled_time)

        reason_block = ""
        if reason and reason.strip():
            reason_block = f"""
            <div style="background-color: rgba(55, 48, 52, 0.4); border-left: 3px solid #914F51; border-radius: 4px; padding: 14px 18px; margin: 20px 0;">
              <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 800; color: #C5A49B; text-transform: uppercase; letter-spacing: 0.5px;">Cancellation Note:</p>
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #EFE9E3;">{reason.strip()}</p>
            </div>
            """

        body = f"""
        <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
          Interview Cancelled
        </h1>
        <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          Hello <strong style="color: #EFE9E3;">{candidate_name or 'Candidate'}</strong>,
        </p>
        <p style="margin: 0 0 18px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
          This is an official notice that your scheduled interview for <strong style="color: #EFE9E3;">{job_title}</strong> at <strong style="color: #EFE9E3;">{company_name}</strong> (originally set for {time_display}) has been cancelled.
        </p>

        {reason_block}

        <p style="margin: 18px 0 0 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
          If this position is to be rescheduled, our recruitment team will reach out with a new schedule. You can check the current status of your application in your SkillSphere dashboard.
        </p>

        <p style="margin: 24px 0 0 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
          Best regards,<br>
          <strong style="color: #EFE9E3;">The {company_name} Talent Team & SkillSphere</strong>
        </p>
        """

        html_content = _wrap_email_template(f"Interview Cancelled — {job_title}", "Interview Status Update", body)
        return cls._dispatch_brevo_email(
            subject=subject,
            to_email=to_email,
            user_name=candidate_name,
            html_content=html_content,
            email_type="INTERVIEW_CANCELLED",
            metadata={
                "job_title": job_title,
                "company_name": company_name,
                "cancelled_time": str(scheduled_time)
            },
            force_mock=force_mock
        )

    @classmethod
    def send_assessment_decision_email(
        cls,
        to_email: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        assessment_title: str,
        decision: str,  # ACCEPTED, REJECTED, MOVED_TO_INTERVIEW, ON_HOLD
        candidate_message: Optional[str] = None,
        force_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch candidate notification for a recruiter's assessment evaluation decision via Brevo.
        Enforces privacy: Never includes scores, percentages, internal remarks, or answer keys.
        HOLD decisions do not send an external email.
        """
        decision_upper = decision.upper()

        if decision_upper == "ON_HOLD":
            return {
                "status": "skipped",
                "mode": "skipped",
                "delivered": False,
                "email_type": "ASSESSMENT_DECISION_ON_HOLD",
                "detail": "HOLD decisions do not trigger external email dispatch."
            }

        dashboard_link = f"{settings.FRONTEND_BASE_URL}/dashboard?tab=applications"

        custom_msg_block = ""
        if candidate_message and candidate_message.strip():
            custom_msg_block = f"""
            <div style="background-color: rgba(55, 48, 52, 0.4); border-left: 3px solid #914F51; border-radius: 4px; padding: 14px 18px; margin: 20px 0;">
              <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 800; color: #C5A49B; text-transform: uppercase; letter-spacing: 0.5px;">Message from Hiring Team:</p>
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #EFE9E3;">{candidate_message.strip()}</p>
            </div>
            """

        if decision_upper == "ACCEPTED":
            subject = f"Congratulations! Assessment Shortlisted — {job_title} | SkillSphere"
            preheader = "Assessment Reviewed & Shortlisted"
            body = f"""
            <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
              Assessment Reviewed &bull; Shortlisted
            </h1>
            <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
              Hello <strong style="color: #EFE9E3;">{candidate_name or 'Candidate'}</strong>,
            </p>
            <p style="margin: 0 0 18px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
              Congratulations! Your assessment for <strong style="color: #EFE9E3;">{job_title}</strong> at <strong style="color: #EFE9E3;">{company_name}</strong> has been reviewed by the recruitment team, and you have been shortlisted for the next stage.
            </p>

            {custom_msg_block}

            <div style="background-color: rgba(55, 48, 52, 0.6); border: 1px solid rgba(197, 164, 155, 0.25); border-radius: 14px; padding: 20px; margin: 24px 0;">
              <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 700; color: #EFE9E3; text-transform: uppercase; letter-spacing: 0.5px;">
                &#9889; What Happens Next
              </p>
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
                The recruitment team will share details regarding the upcoming steps shortly. Please keep an eye on your email and dashboard notifications.
              </p>
            </div>

            <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 26px 0;">
              <tr>
                <td align="center" style="border-radius: 12px; background-color: #914F51;">
                  <a href="{dashboard_link}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 13px; font-weight: 700; color: #EFE9E3; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 12px; border: 1px solid #C5A49B;">
                    Go to Candidate Dashboard &rarr;
                  </a>
                </td>
              </tr>
            </table>

            <p style="margin: 24px 0 0 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
              Warm regards,<br>
              <strong style="color: #EFE9E3;">The {company_name} Talent Team & SkillSphere</strong>
            </p>
            """

        elif decision_upper == "MOVED_TO_INTERVIEW":
            subject = f"Progressed to Interview Stage — {job_title} | SkillSphere"
            preheader = "Next Stage: Interview"
            body = f"""
            <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
              Progressed to Interview Stage
            </h1>
            <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
              Hello <strong style="color: #EFE9E3;">{candidate_name or 'Candidate'}</strong>,
            </p>
            <p style="margin: 0 0 18px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
              Great news! Following the evaluation of your first-round assessment, you have successfully progressed to the interview stage for <strong style="color: #EFE9E3;">{job_title}</strong> at <strong style="color: #EFE9E3;">{company_name}</strong>.
            </p>

            {custom_msg_block}

            <div style="background-color: rgba(55, 48, 52, 0.6); border: 1px solid rgba(197, 164, 155, 0.25); border-radius: 14px; padding: 20px; margin: 24px 0;">
              <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 700; color: #EFE9E3; text-transform: uppercase; letter-spacing: 0.5px;">
                &#128197; Interview Scheduling Details
              </p>
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
                You will receive a separate invitation with your scheduled date, time, and meeting link as soon as your interviewer confirms availability.
              </p>
            </div>

            <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 26px 0;">
              <tr>
                <td align="center" style="border-radius: 12px; background-color: #914F51;">
                  <a href="{dashboard_link}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 13px; font-weight: 700; color: #EFE9E3; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 12px; border: 1px solid #C5A49B;">
                    View Dashboard &rarr;
                  </a>
                </td>
              </tr>
            </table>

            <p style="margin: 24px 0 0 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
              Best regards,<br>
              <strong style="color: #EFE9E3;">The {company_name} Talent Team & SkillSphere</strong>
            </p>
            """

        else:  # REJECTED
            subject = f"SkillSphere Application Update — {job_title}"
            preheader = "Application Update"
            body = f"""
            <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 800; line-height: 1.3; color: #EFE9E3;">
              Application Status Update
            </h1>
            <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
              Hello <strong style="color: #EFE9E3;">{candidate_name or 'Candidate'}</strong>,
            </p>
            <p style="margin: 0 0 18px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
              Thank you for participating in the assessment for the <strong style="color: #EFE9E3;">{job_title}</strong> role at <strong style="color: #EFE9E3;">{company_name}</strong>.
            </p>
            <p style="margin: 0 0 18px 0; font-size: 14px; line-height: 1.6; color: #C5A49B;">
              After reviewing your application and assessment, the recruitment team has decided not to proceed with your application at this stage. We truly appreciate the time and effort you dedicated to completing the evaluation.
            </p>

            {custom_msg_block}

            <p style="margin: 20px 0 0 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
              We encourage you to explore other openings on SkillSphere that match your profile and skill set. We wish you every success in your career journey.
            </p>

            <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 26px 0;">
              <tr>
                <td align="center" style="border-radius: 12px; background-color: #242023; border: 1px solid rgba(197, 164, 155, 0.3);">
                  <a href="{dashboard_link}" target="_blank" style="display: inline-block; padding: 12px 28px; font-size: 12px; font-weight: 700; color: #EFE9E3; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px;">
                    View Applications &rarr;
                  </a>
                </td>
              </tr>
            </table>

            <p style="margin: 24px 0 0 0; font-size: 13px; line-height: 1.6; color: #C5A49B;">
              Sincerely,<br>
              <strong style="color: #EFE9E3;">The {company_name} Talent Team & SkillSphere</strong>
            </p>
            """

        html_content = _wrap_email_template(subject, preheader, body)
        return cls._dispatch_brevo_email(
            subject=subject,
            to_email=to_email,
            user_name=candidate_name,
            html_content=html_content,
            email_type=f"ASSESSMENT_DECISION_{decision_upper}",
            metadata={
                "job_title": job_title,
                "company_name": company_name,
                "decision": decision_upper
            },
            force_mock=force_mock
        )
