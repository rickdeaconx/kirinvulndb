# Kirin Vulnerability Database API Documentation

**Copyright © 2025 Rick Deacon, Knostic AI - https://knostic.ai**

## Overview

The Kirin Vulnerability Database API provides comprehensive access to AI tool vulnerabilities, remediation services, WordPress integration, and RSS feeds. This API is designed specifically for AI security monitoring and automated remediation through the Kirin plugin ecosystem.

**Base URL:** `http://localhost:8080` (Development) | `https://api.knostic.ai` (Production)

## Table of Contents

1. [Authentication](#authentication)
2. [Core Vulnerability APIs](#core-vulnerability-apis)
3. [Kirin Plugin Integration API](#kirin-plugin-integration-api)
4. [WordPress Integration API](#wordpress-integration-api)
5. [RSS Feed APIs](#rss-feed-apis)
6. [Monitoring & Health APIs](#monitoring--health-apis)
7. [WebSocket APIs](#websocket-apis)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Examples](#examples)

---

## Authentication

### API Key Authentication
Most endpoints require authentication via headers:

- **Kirin Plugin API:** `X-Kirin-Key: kirin-cursor-plugin-v1`
- **WordPress API:** `X-WordPress-Key: wp-integration-v1` 
- **Admin APIs:** `Authorization: Bearer <admin-token>`

### Public Endpoints
The following endpoints are publicly accessible:
- Health checks (`/api/health/*`)
- RSS feeds (`/api/rss/*`)
- Basic vulnerability stats (`/api/vulnerabilities/stats`)
- Main dashboard (`/`)

---

## Core Vulnerability APIs

### GET /api/vulnerabilities

Get paginated list of vulnerabilities with filtering options.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Max records to return (default: 10, max: 100)
- `severity` (string): Filter by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
- `tool` (string): Filter by AI tool name
- `patch_status` (string): Filter by patch status (`unpatched`, `patch_available`, `patched`, `wont_fix`)
- `since` (datetime): Get vulnerabilities since this timestamp

**Response:**
```json
{
  "vulnerabilities": [
    {
      "vulnerability_id": "CVE-2025-54132",
      "cve_id": "CVE-2025-54132", 
      "title": "Cursor IDE Mermaid XSS Vulnerability",
      "description": "Cursor allows embedding images...",
      "severity": "MEDIUM",
      "cvss_score": 4.4,
      "patch_status": "unpatched",
      "affected_tools": ["cursor"],
      "attack_vectors": ["injection"],
      "discovery_date": "2025-09-09T14:43:04.570020",
      "references": ["https://github.com/cursor/cursor/security/advisories/..."],
      "kirin_remediation_available": true,
      "auto_remediation_possible": true,
      "confidence_score": 0.8
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 10
}
```

### GET /api/vulnerabilities/{vulnerability_id}

Get detailed information about a specific vulnerability.

**Response:**
```json
{
  "vulnerability_id": "CVE-2025-54132",
  "cve_id": "CVE-2025-54132",
  "title": "Cursor IDE Mermaid XSS Vulnerability",
  "description": "Detailed description...",
  "severity": "MEDIUM",
  "cvss_score": 4.4,
  "technical_details": "Technical analysis...",
  "affected_versions": ["< 1.3"],
  "fixed_versions": ["1.3+"],
  "patch_status": "patch_available",
  "affected_tools": [
    {
      "id": 1,
      "name": "cursor",
      "description": "AI-powered code editor",
      "category": "code_editor",
      "vendor": "Cursor Inc"
    }
  ],
  "attack_vectors": ["injection", "xss"],
  "references": ["https://..."],
  "poc_available": false,
  "exploit_in_wild": false,
  "discovery_date": "2025-09-09T14:43:04.570020",
  "created_at": "2025-09-09T14:43:04.570020",
  "updated_at": "2025-09-10T10:30:15.123456"
}
```

### GET /api/vulnerabilities/stats

Get vulnerability statistics and distributions.

**Query Parameters:**
- `period_days` (int): Statistics period in days (default: 30, max: 365)

**Response:**
```json
{
  "period_days": 30,
  "total_vulnerabilities": 60,
  "recent_vulnerabilities": 45,
  "severity_distribution": {
    "CRITICAL": 10,
    "HIGH": 23,
    "MEDIUM": 10,
    "LOW": 17,
    "INFO": 0
  },
  "patch_status_distribution": {
    "unpatched": 44,
    "patch_available": 3,
    "patched": 13,
    "wont_fix": 0
  },
  "tool_distribution": {
    "cursor": 20,
    "github_copilot": 21,
    "amazon_codewhisperer": 3,
    "tabnine": 3,
    "codeium": 7
  },
  "generated_at": "2025-09-10T15:31:59.235560"
}
```

---

## Kirin Plugin Integration API

**Authentication Required:** `X-Kirin-Key: kirin-cursor-plugin-v1`

### GET /api/kirin-plugin/health

Health check for Kirin plugin integration.

**Response:**
```json
{
  "status": "healthy",
  "service": "Kirin Plugin API",
  "supported_tools": ["cursor"],
  "api_version": "1.0.0",
  "powered_by": "Knostic AI - https://knostic.ai"
}
```

### GET /api/kirin-plugin/cursor/vulnerabilities

Get Cursor-specific vulnerabilities for Kirin plugin.

**Query Parameters:**
- `since` (datetime): Get vulnerabilities since this timestamp
- `unpatched_only` (bool): Only include unpatched vulnerabilities (default: true)
- `limit` (int): Maximum results (default: 50, max: 200)

**Response:**
```json
{
  "vulnerabilities": [
    {
      "vulnerability_id": "CVE-2025-54132",
      "cve_id": "CVE-2025-54132",
      "title": "Cursor IDE Mermaid XSS",
      "description": "Vulnerability description...",
      "severity": "MEDIUM",
      "cvss_score": 4.4,
      "discovery_date": "2025-09-09T14:43:04.570020",
      "patch_status": "unpatched",
      "attack_vectors": ["injection"],
      "technical_details": "Technical details...",
      "affected_versions": [],
      "fixed_versions": [],
      "references": ["https://..."],
      "kirin_remediation_available": true,
      "can_auto_remediate": true,
      "confidence_score": 0.8
    }
  ],
  "total_found": 20,
  "cursor_specific": true,
  "generated_at": "2025-09-10T15:31:35.558362",
  "kirin_plugin_version": "1.0.0"
}
```

### POST /api/kirin-plugin/cursor/remediate/{vulnerability_id}

Request AI-powered remediation for a Cursor vulnerability.

**Request Body:**
```json
{
  "workspace_info": {
    "project_path": "/Users/dev/project",
    "language": "javascript",
    "framework": "react",
    "cursor_version": "1.2.0",
    "extensions": ["prettier", "eslint"]
  },
  "cursor_version": "1.2.0",
  "priority": "high",
  "auto_apply": false
}
```

**Response:**
```json
{
  "vulnerability_id": "CVE-2025-54132",
  "remediation_id": "kirin-dcbfcb22",
  "steps": [
    {
      "step_id": "injection-1",
      "step_type": "automated",
      "title": "Enable Input Validation",
      "description": "Activate strict input validation for Cursor",
      "command": "cursor.enableInputValidation",
      "expected_outcome": "Input validation enabled",
      "risk_level": "low",
      "estimated_seconds": 30,
      "prerequisites": []
    }
  ],
  "automated_actions": [
    {
      "action_id": "enable-input-validation",
      "action_type": "setting_change",
      "target": "cursor.security.inputValidation",
      "old_value": "basic",
      "new_value": "strict",
      "reversible": true,
      "backup_location": null
    }
  ],
  "manual_actions": [
    {
      "action_id": "code-review",
      "title": "Code Input Review",
      "description": "Review recent code inputs for injection patterns",
      "instructions": [
        "Check recent code changes",
        "Look for suspicious input patterns"
      ],
      "verification_steps": [
        "Code inputs reviewed",
        "Input validation updated"
      ],
      "estimated_minutes": 15
    }
  ],
  "risk_level": "medium",
  "estimated_time_minutes": 5,
  "requires_restart": false,
  "backup_recommended": false,
  "success_indicators": [
    "Vulnerability CVE-2025-54132 remediation applied",
    "No security warnings in Cursor"
  ],
  "rollback_steps": [
    "Revert cursor.security.inputValidation to basic"
  ],
  "generated_at": "2025-09-10T15:31:43.292128",
  "expires_at": "2025-09-11T15:31:43.288047",
  "kirin_compatible": true
}
```

### GET /api/kirin-plugin/cursor/remediation-status/{remediation_id}

Get status of a remediation action.

**Response:**
```json
{
  "remediation_id": "kirin-dcbfcb22",
  "status": "available",
  "message": "Remediation steps ready for Kirin plugin execution",
  "kirin_plugin_compatible": true,
  "cursor_specific": true
}
```

### POST /api/kirin-plugin/cursor/report-remediation

Report remediation results back from Kirin plugin.

**Request Body:**
```json
{
  "remediation_id": "kirin-dcbfcb22",
  "success": true,
  "executed_actions": ["enable-input-validation"],
  "failed_actions": [],
  "error_message": null,
  "execution_time_seconds": 45
}
```

**Response:**
```json
{
  "acknowledged": true,
  "remediation_id": "kirin-dcbfcb22",
  "message": "Remediation result recorded",
  "timestamp": "2025-09-10T15:31:43.292128"
}
```

---

## WordPress Integration API

**Authentication Required:** `X-WordPress-Key: wp-integration-v1`

### GET /api/wordpress/vulnerabilities

Get vulnerabilities formatted for WordPress consumption.

**Query Parameters:**
- `limit` (int): Max results (default: 20, max: 100)
- `since_days` (int): Get vulnerabilities from last N days (default: 7, max: 30)
- `format` (string): Response format (`json`, `html`) (default: `json`)

**Response:**
```json
{
  "posts": [
    {
      "title": "Cursor IDE Security Alert: CVE-2025-54132",
      "content": "<h3>Security Vulnerability Detected</h3><p>Description...</p>",
      "excerpt": "Cursor IDE has a medium severity vulnerability...",
      "post_type": "vulnerability_alert",
      "meta": {
        "cve_id": "CVE-2025-54132",
        "severity": "MEDIUM",
        "cvss_score": 4.4,
        "affected_tools": ["cursor"],
        "patch_status": "unpatched"
      },
      "categories": ["Security", "AI Tools", "Cursor"],
      "tags": ["vulnerability", "cursor", "injection", "medium"],
      "publish_date": "2025-09-09T14:43:04.570020",
      "author": "Kirin VulnDB"
    }
  ],
  "total": 15,
  "generated_at": "2025-09-10T15:31:59.235560"
}
```

### POST /api/wordpress/webhook

Webhook endpoint for WordPress integration events.

**Request Body:**
```json
{
  "event": "vulnerability_published",
  "vulnerability_id": "CVE-2025-54132",
  "wordpress_post_id": 1234,
  "timestamp": "2025-09-10T15:31:59.235560"
}
```

**Response:**
```json
{
  "acknowledged": true,
  "event": "vulnerability_published",
  "processed_at": "2025-09-10T15:31:59.235560"
}
```

---

## RSS Feed APIs

**Public Access - No Authentication Required**

### GET /api/rss/vulnerabilities.xml

RSS feed for all AI tool vulnerabilities - WordPress compatible.

**Query Parameters:**
- `limit` (int): Max vulnerabilities (default: 50, max: 200)  
- `since_days` (int): Get vulnerabilities from last N days (default: 30, max: 365)
- `severity` (string): Filter by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
- `tool` (string): Filter by AI tool name
- `patch_status` (string): Filter by patch status

**Response:** XML RSS 2.0 format
```xml
<?xml version="1.0"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Kirin Vulnerability Database - AI Security Feed</title>
    <link>https://knostic.ai</link>
    <description>Latest AI tool vulnerabilities and security alerts from Kirin VulnDB</description>
    <language>en-us</language>
    <managingEditor>rick@knostic.ai (Rick Deacon)</managingEditor>
    <generator>Kirin VulnDB by Knostic AI</generator>
    <item>
      <title>CVE-2025-54132: MEDIUM Vulnerability in Cursor</title>
      <link>https://knostic.ai/vulnerability/CVE-2025-54132</link>
      <description><![CDATA[HTML content for WordPress import...]]></description>
      <content:encoded><![CDATA[Full HTML article content...]]></content:encoded>
      <pubDate>Wed, 10 Sep 2025 15:33:46 GMT</pubDate>
      <guid isPermaLink="false">CVE-2025-54132</guid>
      <category>Security</category>
      <category>Cursor IDE</category>
      <dc:creator>Kirin VulnDB</dc:creator>
    </item>
  </channel>
</rss>
```

### GET /api/rss/cursor-vulnerabilities.xml

RSS feed specifically for Cursor IDE vulnerabilities.

**Query Parameters:**
- `limit` (int): Max vulnerabilities (default: 50, max: 200)
- `since_days` (int): Get vulnerabilities from last N days (default: 30, max: 365)
- `severity` (string): Filter by severity

**Response:** XML RSS 2.0 format optimized for Cursor security blog posts.

### GET /api/rss/feed-info

Information about available RSS feeds.

**Response:**
```json
{
  "feeds": {
    "all_vulnerabilities": {
      "url": "/api/rss/vulnerabilities.xml",
      "description": "All AI tool vulnerabilities",
      "parameters": [
        "limit (max 200, default 50)",
        "since_days (max 365, default 30)",
        "severity (CRITICAL, HIGH, MEDIUM, LOW)",
        "tool (filter by AI tool name)",
        "patch_status (unpatched, patch_available, patched, wont_fix)"
      ]
    },
    "cursor_vulnerabilities": {
      "url": "/api/rss/cursor-vulnerabilities.xml", 
      "description": "Cursor IDE specific vulnerabilities"
    }
  },
  "wordpress_integration": {
    "description": "These RSS feeds are optimized for WordPress import",
    "features": [
      "HTML formatted content",
      "Proper categories/tags",
      "Publication dates",
      "Unique GUIDs",
      "SEO-friendly titles"
    ]
  }
}
```

---

## Monitoring & Health APIs

### GET /api/health

Overall system health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-10T15:31:59.235560",
  "services": {
    "database": "healthy",
    "vulnerability_monitor": "active",
    "websocket_manager": "active",
    "kirin_plugin": "healthy"
  },
  "version": "1.0.0",
  "uptime_seconds": 3661
}
```

### GET /api/monitoring/system

System monitoring metrics.

**Response:**
```json
{
  "cpu_usage": 15.2,
  "memory_usage": 245.6,
  "disk_usage": 12.3,
  "active_connections": 15,
  "requests_per_minute": 45,
  "vulnerability_scan_status": {
    "last_scan": "2025-09-10T11:32:46.000000",
    "next_scan": "2025-09-11T11:32:46.000000",
    "vulnerabilities_found": 62,
    "new_since_last": 2
  },
  "generated_at": "2025-09-10T15:31:59.235560"
}
```

---

## WebSocket APIs

### WS /api/ws/vulnerabilities

Real-time vulnerability updates via WebSocket.

**Connection:** `ws://localhost:8080/api/ws/vulnerabilities`

**Messages Received:**
```json
{
  "type": "vulnerability_discovered",
  "data": {
    "vulnerability_id": "CVE-2025-54133",
    "severity": "HIGH",
    "affected_tools": ["cursor"],
    "discovery_date": "2025-09-10T15:31:59.235560"
  }
}
```

```json
{
  "type": "remediation_available", 
  "data": {
    "vulnerability_id": "CVE-2025-54132",
    "remediation_id": "kirin-abc123",
    "auto_remediation_possible": true
  }
}
```

---

## Error Handling

All APIs use standard HTTP status codes and return consistent error responses:

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "VULNERABILITY_NOT_FOUND",
  "timestamp": "2025-09-10T15:31:59.235560",
  "request_id": "req_abc123"
}
```

### Common Status Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required/failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Rate Limiting

API endpoints are rate limited to ensure fair usage:

- **General APIs:** 1000 requests/hour per IP
- **Kirin Plugin API:** 5000 requests/hour per API key
- **RSS Feeds:** 100 requests/hour per IP (cached for 1 hour)
- **WebSocket Connections:** 10 concurrent connections per IP

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1725984719
```

---

## Examples

### WordPress RSS Import
To import vulnerabilities into WordPress as blog posts:

1. **Add RSS feed to WordPress:**
   ```
   Feed URL: https://api.knostic.ai/api/rss/cursor-vulnerabilities.xml
   ```

2. **Configure import settings:**
   - Post Type: `post` or `security_alert`
   - Categories: Map RSS categories to WordPress categories
   - Author: Set to security team member
   - Status: `draft` for review, `publish` for automatic posting

### Kirin Plugin Integration
Example workflow for Kirin plugin:

```javascript
// 1. Get Cursor vulnerabilities
const response = await fetch('/api/kirin-plugin/cursor/vulnerabilities', {
  headers: { 'X-Kirin-Key': 'kirin-cursor-plugin-v1' }
});
const vulnerabilities = await response.json();

// 2. Request remediation for high severity vulnerabilities
for (const vuln of vulnerabilities.vulnerabilities) {
  if (vuln.severity === 'HIGH' && vuln.can_auto_remediate) {
    const remediation = await fetch(`/api/kirin-plugin/cursor/remediate/${vuln.vulnerability_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Kirin-Key': 'kirin-cursor-plugin-v1'
      },
      body: JSON.stringify({
        workspace_info: {
          project_path: '/current/project',
          language: 'typescript',
          cursor_version: '1.2.0'
        },
        priority: 'high'
      })
    });
    
    // 3. Execute remediation steps
    const steps = await remediation.json();
    // Execute automated actions...
    
    // 4. Report results back
    await fetch('/api/kirin-plugin/cursor/report-remediation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Kirin-Key': 'kirin-cursor-plugin-v1'
      },
      body: JSON.stringify({
        remediation_id: steps.remediation_id,
        success: true
      })
    });
  }
}
```

---

## Support and Contact

For API support and questions:

- **Email:** rick@knostic.ai
- **Website:** https://knostic.ai
- **Documentation:** https://docs.knostic.ai
- **GitHub Issues:** https://github.com/knostic-ai/kirin-vulndb/issues

**Powered by Knostic AI - Advanced AI Security Solutions**