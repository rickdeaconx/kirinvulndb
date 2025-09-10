"""
AI Remediation Service for Cursor Vulnerabilities
Generates AI-powered remediation steps for Kirin plugin integration
Copyright © 2025 Rick Deacon, Knostic AI - https://knostic.ai
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.schemas.kirin import (
    CursorKirinRemediationResponse, RemediationStep, AutomatedAction, ManualAction,
    RemediationStepType, RemediationRiskLevel, WorkspaceInfo
)
from app.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

class AIRemediationService:
    """AI-powered remediation service specifically for Cursor vulnerabilities"""
    
    def __init__(self):
        self.supported_attack_vectors = {
            "prompt_injection": self._generate_prompt_injection_remediation,
            "code_execution": self._generate_code_execution_remediation,
            "data_exfiltration": self._generate_data_exfiltration_remediation,
            "privilege_escalation": self._generate_privilege_escalation_remediation,
            "injection": self._generate_injection_remediation
        }
    
    async def generate_cursor_remediation(
        self, 
        vulnerability: Vulnerability, 
        workspace_info: WorkspaceInfo,
        current_version: str
    ) -> CursorKirinRemediationResponse:
        """Generate AI-powered remediation for Cursor vulnerability"""
        
        remediation_id = f"kirin-{uuid.uuid4().hex[:8]}"
        logger.info(f"Generating remediation {remediation_id} for {vulnerability.vulnerability_id}")
        
        # Determine primary attack vector
        primary_attack_vector = self._get_primary_attack_vector(vulnerability)
        
        # Generate remediation based on attack vector
        if primary_attack_vector in self.supported_attack_vectors:
            remediation_generator = self.supported_attack_vectors[primary_attack_vector]
            steps, automated_actions, manual_actions, risk_level = await remediation_generator(
                vulnerability, workspace_info, current_version
            )
        else:
            # Default generic remediation
            steps, automated_actions, manual_actions, risk_level = await self._generate_generic_remediation(
                vulnerability, workspace_info, current_version
            )
        
        # Calculate estimated time
        estimated_time = sum(step.estimated_seconds for step in steps) // 60
        
        # Generate success indicators and rollback steps
        success_indicators = self._generate_success_indicators(vulnerability, automated_actions)
        rollback_steps = self._generate_rollback_steps(automated_actions)
        
        return CursorKirinRemediationResponse(
            vulnerability_id=vulnerability.vulnerability_id,
            remediation_id=remediation_id,
            steps=steps,
            automated_actions=automated_actions,
            manual_actions=manual_actions,
            risk_level=risk_level,
            estimated_time_minutes=max(estimated_time, 5),
            requires_restart=self._requires_cursor_restart(automated_actions),
            backup_recommended=risk_level in [RemediationRiskLevel.HIGH, RemediationRiskLevel.CRITICAL],
            success_indicators=success_indicators,
            rollback_steps=rollback_steps,
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            kirin_compatible=True
        )
    
    def _get_primary_attack_vector(self, vulnerability: Vulnerability) -> str:
        """Determine the primary attack vector for the vulnerability"""
        if not vulnerability.attack_vectors:
            return "generic"
        
        # Priority order for attack vectors
        priority_order = ["prompt_injection", "code_execution", "privilege_escalation", "data_exfiltration", "injection"]
        
        for vector in priority_order:
            if any(vector in av.lower() if isinstance(av, str) else str(av).lower() for av in vulnerability.attack_vectors):
                return vector
        
        return vulnerability.attack_vectors[0] if vulnerability.attack_vectors else "generic"
    
    async def _generate_prompt_injection_remediation(
        self, vulnerability: Vulnerability, workspace_info: WorkspaceInfo, current_version: str
    ) -> tuple[List[RemediationStep], List[AutomatedAction], List[ManualAction], RemediationRiskLevel]:
        """Generate remediation for prompt injection vulnerabilities"""
        
        steps = [
            RemediationStep(
                step_id="prompt-injection-1",
                step_type=RemediationStepType.AUTOMATED,
                title="Disable AI Code Suggestions",
                description="Temporarily disable AI code completion to prevent prompt injection",
                command="cursor.disableAISuggestions",
                expected_outcome="AI suggestions disabled in Cursor",
                risk_level=RemediationRiskLevel.LOW,
                estimated_seconds=30
            ),
            RemediationStep(
                step_id="prompt-injection-2",
                step_type=RemediationStepType.MANUAL,
                title="Review Recent AI Interactions",
                description="Check recent AI code suggestions for suspicious patterns",
                instructions="Review AI interaction history for unexpected code suggestions",
                expected_outcome="Suspicious AI interactions identified",
                risk_level=RemediationRiskLevel.MEDIUM,
                estimated_seconds=300
            ),
            RemediationStep(
                step_id="prompt-injection-3",
                step_type=RemediationStepType.AUTOMATED,
                title="Update Security Settings",
                description="Enable stricter AI safety controls",
                command="cursor.updateSecuritySettings",
                expected_outcome="Enhanced security settings applied",
                risk_level=RemediationRiskLevel.LOW,
                estimated_seconds=60
            )
        ]
        
        automated_actions = [
            AutomatedAction(
                action_id="disable-ai-suggestions",
                action_type="setting_change",
                target="cursor.ai.enabled",
                old_value="true",
                new_value="false",
                reversible=True,
                backup_location="~/.cursor/backup/ai_settings.json"
            ),
            AutomatedAction(
                action_id="enable-ai-safety",
                action_type="setting_change", 
                target="cursor.ai.safetyMode",
                old_value="standard",
                new_value="strict",
                reversible=True
            )
        ]
        
        manual_actions = [
            ManualAction(
                action_id="review-ai-history",
                title="Review AI Interaction History",
                description="Manually review recent AI code suggestions",
                instructions=[
                    "Open Cursor AI history panel",
                    "Look for unusual or suspicious code suggestions",
                    "Check for code that doesn't match your project patterns",
                    "Report any suspicious findings"
                ],
                verification_steps=[
                    "AI history reviewed",
                    "Suspicious patterns documented",
                    "Security team notified if needed"
                ],
                estimated_minutes=10
            )
        ]
        
        return steps, automated_actions, manual_actions, RemediationRiskLevel.MEDIUM
    
    async def _generate_code_execution_remediation(
        self, vulnerability: Vulnerability, workspace_info: WorkspaceInfo, current_version: str
    ) -> tuple[List[RemediationStep], List[AutomatedAction], List[ManualAction], RemediationRiskLevel]:
        """Generate remediation for code execution vulnerabilities"""
        
        steps = [
            RemediationStep(
                step_id="code-exec-1",
                step_type=RemediationStepType.AUTOMATED,
                title="Disable Extension Auto-Execution",
                description="Prevent automatic execution of untrusted extensions",
                command="cursor.disableExtensionAutoExec",
                expected_outcome="Extension auto-execution disabled",
                risk_level=RemediationRiskLevel.HIGH,
                estimated_seconds=45
            ),
            RemediationStep(
                step_id="code-exec-2",
                step_type=RemediationStepType.VERIFICATION,
                title="Scan for Malicious Extensions",
                description="Check installed extensions for security issues",
                command="cursor.scanExtensions",
                expected_outcome="Extension security scan completed",
                risk_level=RemediationRiskLevel.MEDIUM,
                estimated_seconds=120
            )
        ]
        
        automated_actions = [
            AutomatedAction(
                action_id="disable-auto-exec",
                action_type="setting_change",
                target="cursor.extensions.autoExecute",
                old_value="true",
                new_value="false",
                reversible=True
            )
        ]
        
        manual_actions = [
            ManualAction(
                action_id="extension-audit",
                title="Manual Extension Audit",
                description="Review and validate all installed extensions",
                instructions=[
                    "Open Extensions panel in Cursor",
                    "Review each installed extension",
                    "Disable or remove suspicious extensions",
                    "Keep only necessary and trusted extensions"
                ],
                verification_steps=[
                    "All extensions reviewed",
                    "Suspicious extensions removed",
                    "Extension list documented"
                ],
                estimated_minutes=15
            )
        ]
        
        return steps, automated_actions, manual_actions, RemediationRiskLevel.HIGH
    
    async def _generate_generic_remediation(
        self, vulnerability: Vulnerability, workspace_info: WorkspaceInfo, current_version: str
    ) -> tuple[List[RemediationStep], List[AutomatedAction], List[ManualAction], RemediationRiskLevel]:
        """Generate generic remediation steps"""
        
        steps = [
            RemediationStep(
                step_id="generic-1",
                step_type=RemediationStepType.AUTOMATED,
                title="Update Cursor to Latest Version",
                description="Ensure Cursor is updated to the latest secure version",
                command="cursor.checkForUpdates",
                expected_outcome="Cursor updated to latest version",
                risk_level=RemediationRiskLevel.LOW,
                estimated_seconds=180
            ),
            RemediationStep(
                step_id="generic-2",
                step_type=RemediationStepType.MANUAL,
                title="Review Security Settings",
                description="Verify Cursor security configuration",
                instructions="Check and update Cursor security settings",
                expected_outcome="Security settings optimized",
                risk_level=RemediationRiskLevel.LOW,
                estimated_seconds=300
            )
        ]
        
        automated_actions = [
            AutomatedAction(
                action_id="update-cursor",
                action_type="software_update",
                target="cursor.application",
                old_value=current_version,
                new_value="latest",
                reversible=False
            )
        ]
        
        manual_actions = [
            ManualAction(
                action_id="security-review",
                title="Security Settings Review",
                description="Review and optimize Cursor security settings",
                instructions=[
                    "Open Cursor settings",
                    "Navigate to Security section",
                    "Enable recommended security features",
                    "Disable unnecessary network features"
                ],
                verification_steps=[
                    "Security settings reviewed",
                    "Recommendations applied",
                    "Changes documented"
                ],
                estimated_minutes=5
            )
        ]
        
        return steps, automated_actions, manual_actions, RemediationRiskLevel.MEDIUM
    
    async def _generate_data_exfiltration_remediation(
        self, vulnerability: Vulnerability, workspace_info: WorkspaceInfo, current_version: str
    ) -> tuple[List[RemediationStep], List[AutomatedAction], List[ManualAction], RemediationRiskLevel]:
        """Generate remediation for data exfiltration vulnerabilities"""
        
        steps = [
            RemediationStep(
                step_id="data-exfil-1",
                step_type=RemediationStepType.AUTOMATED,
                title="Disable Cloud Sync",
                description="Temporarily disable cloud synchronization features",
                command="cursor.disableCloudSync",
                expected_outcome="Cloud sync disabled",
                risk_level=RemediationRiskLevel.MEDIUM,
                estimated_seconds=30
            ),
            RemediationStep(
                step_id="data-exfil-2",
                step_type=RemediationStepType.AUTOMATED,
                title="Enable Data Protection",
                description="Activate enhanced data protection mode",
                command="cursor.enableDataProtection",
                expected_outcome="Data protection activated",
                risk_level=RemediationRiskLevel.LOW,
                estimated_seconds=45
            )
        ]
        
        automated_actions = [
            AutomatedAction(
                action_id="disable-cloud-sync",
                action_type="setting_change",
                target="cursor.sync.enabled",
                old_value="true",
                new_value="false",
                reversible=True
            ),
            AutomatedAction(
                action_id="enable-data-protection",
                action_type="setting_change",
                target="cursor.security.dataProtection",
                old_value="standard",
                new_value="enhanced",
                reversible=True
            )
        ]
        
        manual_actions = [
            ManualAction(
                action_id="audit-data-access",
                title="Audit Data Access Logs",
                description="Review recent data access and transmission logs",
                instructions=[
                    "Check Cursor access logs",
                    "Look for unusual data transmission patterns",
                    "Verify no sensitive data was compromised",
                    "Report any suspicious activity"
                ],
                verification_steps=[
                    "Access logs reviewed",
                    "No suspicious activity found",
                    "Data integrity confirmed"
                ],
                estimated_minutes=20
            )
        ]
        
        return steps, automated_actions, manual_actions, RemediationRiskLevel.HIGH
    
    async def _generate_privilege_escalation_remediation(
        self, vulnerability: Vulnerability, workspace_info: WorkspaceInfo, current_version: str
    ) -> tuple[List[RemediationStep], List[AutomatedAction], List[ManualAction], RemediationRiskLevel]:
        """Generate remediation for privilege escalation vulnerabilities"""
        
        steps = [
            RemediationStep(
                step_id="priv-esc-1",
                step_type=RemediationStepType.AUTOMATED,
                title="Restrict Cursor Permissions",
                description="Reduce Cursor's system permissions to minimum required",
                command="cursor.restrictPermissions",
                expected_outcome="Cursor permissions restricted",
                risk_level=RemediationRiskLevel.MEDIUM,
                estimated_seconds=60
            )
        ]
        
        automated_actions = [
            AutomatedAction(
                action_id="restrict-permissions",
                action_type="permission_change",
                target="cursor.system.permissions",
                old_value="elevated",
                new_value="restricted",
                reversible=True
            )
        ]
        
        manual_actions = [
            ManualAction(
                action_id="permission-audit",
                title="System Permission Audit",
                description="Review system-level permissions granted to Cursor",
                instructions=[
                    "Check system security settings",
                    "Review Cursor's granted permissions",
                    "Revoke unnecessary privileges",
                    "Enable permission monitoring"
                ],
                verification_steps=[
                    "Permissions audited",
                    "Unnecessary privileges revoked",
                    "Monitoring enabled"
                ],
                estimated_minutes=10
            )
        ]
        
        return steps, automated_actions, manual_actions, RemediationRiskLevel.HIGH
    
    async def _generate_injection_remediation(
        self, vulnerability: Vulnerability, workspace_info: WorkspaceInfo, current_version: str
    ) -> tuple[List[RemediationStep], List[AutomatedAction], List[ManualAction], RemediationRiskLevel]:
        """Generate remediation for injection vulnerabilities"""
        
        steps = [
            RemediationStep(
                step_id="injection-1",
                step_type=RemediationStepType.AUTOMATED,
                title="Enable Input Validation",
                description="Activate strict input validation for Cursor",
                command="cursor.enableInputValidation",
                expected_outcome="Input validation enabled",
                risk_level=RemediationRiskLevel.LOW,
                estimated_seconds=30
            )
        ]
        
        automated_actions = [
            AutomatedAction(
                action_id="enable-input-validation",
                action_type="setting_change",
                target="cursor.security.inputValidation",
                old_value="basic",
                new_value="strict",
                reversible=True
            )
        ]
        
        manual_actions = [
            ManualAction(
                action_id="code-review",
                title="Code Input Review",
                description="Review recent code inputs for injection patterns",
                instructions=[
                    "Check recent code changes",
                    "Look for suspicious input patterns", 
                    "Validate all external inputs",
                    "Update input sanitization"
                ],
                verification_steps=[
                    "Code inputs reviewed",
                    "Input validation updated",
                    "No injection vectors found"
                ],
                estimated_minutes=15
            )
        ]
        
        return steps, automated_actions, manual_actions, RemediationRiskLevel.MEDIUM
    
    def _generate_success_indicators(self, vulnerability: Vulnerability, automated_actions: List[AutomatedAction]) -> List[str]:
        """Generate success indicators for remediation verification"""
        indicators = [
            f"Vulnerability {vulnerability.vulnerability_id} remediation applied",
            "No security warnings in Cursor",
            "All automated actions completed successfully"
        ]
        
        for action in automated_actions:
            if action.action_type == "setting_change":
                indicators.append(f"Setting {action.target} updated to {action.new_value}")
            elif action.action_type == "software_update":
                indicators.append("Cursor updated to latest version")
        
        return indicators
    
    def _generate_rollback_steps(self, automated_actions: List[AutomatedAction]) -> List[str]:
        """Generate rollback steps for remediation reversal"""
        rollback_steps = []
        
        for action in automated_actions:
            if action.reversible and action.old_value:
                rollback_steps.append(f"Revert {action.target} to {action.old_value}")
            elif action.backup_location:
                rollback_steps.append(f"Restore from backup: {action.backup_location}")
        
        if not rollback_steps:
            rollback_steps.append("No automatic rollback available - manual restoration required")
        
        return rollback_steps
    
    def _requires_cursor_restart(self, automated_actions: List[AutomatedAction]) -> bool:
        """Check if Cursor restart is required after remediation"""
        restart_required_actions = ["software_update", "extension_disable", "permission_change"]
        
        return any(action.action_type in restart_required_actions for action in automated_actions)