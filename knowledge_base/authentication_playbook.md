# Authentication Incident Playbook
## Triage
Validate alert timestamps, identity-provider source, user, source IP, authentication method, MFA result, device, and baseline behavior. A successful sign-in after repeated failures raises concern but is not proof of compromise.
## Investigation
Correlate sign-in, MFA, endpoint, VPN, and cloud audit records. Confirm whether the user recognizes the activity. Preserve the original records and record query windows.
## Containment
After analyst authorization, revoke active sessions, reset credentials, require strong MFA, block a confirmed malicious indicator, and increase monitoring. Do not disable a business-critical account without considering operational impact.

