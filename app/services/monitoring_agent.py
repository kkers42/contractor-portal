"""
Monitoring Agent - Claude-Powered Application Health Monitor
Monitors application health, diagnoses issues, and performs auto-repair
"""

import os
import requests
import json
import time
from datetime import datetime
from anthropic import Anthropic
import subprocess
import logging

# Setup logging
logging.basicConfig(
    filename='/var/log/monitoring-agent.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')  # Your N8N webhook for bug reports
APP_URL = os.getenv('APP_URL', 'https://snow-contractor.com')
SERVER_HOST = os.getenv('SERVER_HOST', '72.61.0.186')

# Health check endpoints
HEALTH_ENDPOINTS = [
    '/properties/',
    '/users/',
    '/winter-events/',
    '/sms/conversations'
]

class MonitoringAgent:
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.issues_detected = []

    def check_application_health(self):
        """Perform comprehensive health checks on the application"""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": [],
            "errors": []
        }

        # 1. Check if web server is responding
        try:
            response = requests.get(f"{APP_URL}/static/login.html", timeout=10)
            if response.status_code != 200:
                health_report["errors"].append({
                    "type": "web_server",
                    "message": f"Login page returned status {response.status_code}",
                    "severity": "high"
                })
                health_report["status"] = "degraded"
        except Exception as e:
            health_report["errors"].append({
                "type": "web_server",
                "message": f"Cannot reach web server: {str(e)}",
                "severity": "critical"
            })
            health_report["status"] = "down"

        # 2. Check API endpoints (with fake admin token for testing)
        for endpoint in HEALTH_ENDPOINTS:
            try:
                response = requests.get(
                    f"{APP_URL}{endpoint}",
                    timeout=5
                )
                health_report["checks"].append({
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "healthy": response.status_code in [200, 401]  # 401 is OK (auth required)
                })

                if response.status_code == 500:
                    health_report["errors"].append({
                        "type": "api_error",
                        "endpoint": endpoint,
                        "message": "Internal server error",
                        "severity": "high"
                    })
                    health_report["status"] = "degraded"
            except Exception as e:
                health_report["errors"].append({
                    "type": "api_timeout",
                    "endpoint": endpoint,
                    "message": str(e),
                    "severity": "medium"
                })

        # 3. Check database connectivity (via SSH)
        try:
            db_check = subprocess.run(
                ['ssh', f'root@{SERVER_HOST}',
                 'mysql -u contractor -pBimmer325i contractor_portal -e "SELECT 1" 2>/dev/null'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if db_check.returncode != 0:
                health_report["errors"].append({
                    "type": "database",
                    "message": "Database connection failed",
                    "severity": "critical"
                })
                health_report["status"] = "down"
        except Exception as e:
            health_report["errors"].append({
                "type": "database",
                "message": f"Cannot check database: {str(e)}",
                "severity": "high"
            })

        # 4. Check service status
        try:
            service_check = subprocess.run(
                ['ssh', f'root@{SERVER_HOST}',
                 'systemctl is-active contractor-portal'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if service_check.stdout.strip() != 'active':
                health_report["errors"].append({
                    "type": "service",
                    "message": f"Service status: {service_check.stdout.strip()}",
                    "severity": "critical"
                })
                health_report["status"] = "down"
        except Exception as e:
            health_report["errors"].append({
                "type": "service",
                "message": f"Cannot check service status: {str(e)}",
                "severity": "high"
            })

        # 5. Check disk space
        try:
            disk_check = subprocess.run(
                ['ssh', f'root@{SERVER_HOST}',
                 'df -h / | tail -1 | awk \'{print $5}\' | sed \'s/%//\''],
                capture_output=True,
                text=True,
                timeout=10
            )
            disk_usage = int(disk_check.stdout.strip())
            if disk_usage > 90:
                health_report["errors"].append({
                    "type": "disk_space",
                    "message": f"Disk usage at {disk_usage}%",
                    "severity": "high"
                })
            elif disk_usage > 80:
                health_report["errors"].append({
                    "type": "disk_space",
                    "message": f"Disk usage at {disk_usage}%",
                    "severity": "medium"
                })
        except Exception as e:
            logging.warning(f"Could not check disk space: {e}")

        # 6. Check memory usage
        try:
            mem_check = subprocess.run(
                ['ssh', f'root@{SERVER_HOST}',
                 'free | grep Mem | awk \'{print int($3/$2 * 100)}\''],
                capture_output=True,
                text=True,
                timeout=10
            )
            mem_usage = int(mem_check.stdout.strip())
            if mem_usage > 90:
                health_report["errors"].append({
                    "type": "memory",
                    "message": f"Memory usage at {mem_usage}%",
                    "severity": "medium"
                })
        except Exception as e:
            logging.warning(f"Could not check memory: {e}")

        return health_report

    def diagnose_with_claude(self, health_report):
        """Use Claude to analyze health report and suggest fixes"""

        if not health_report["errors"]:
            return None

        prompt = f"""You are a senior DevOps engineer analyzing a health check report for a snow contractor management application.

HEALTH REPORT:
{json.dumps(health_report, indent=2)}

CONTEXT:
- Application: FastAPI backend with MySQL database
- Server: Ubuntu Linux (root@{SERVER_HOST})
- Service: contractor-portal.service (systemd)
- Stack: Python/FastAPI, MySQL, Nginx

Analyze the errors and provide:
1. Root cause analysis for each error
2. Severity assessment (critical/high/medium/low)
3. Recommended actions to fix each issue
4. Whether automatic repair is safe or requires manual intervention
5. Shell commands to execute for auto-repair (if safe)

Respond in JSON format:
{{
  "diagnosis": "Brief summary of the problem",
  "severity": "critical|high|medium|low",
  "root_cause": "Explanation of what's wrong",
  "auto_repair_safe": true/false,
  "repair_actions": [
    {{
      "description": "What this action does",
      "command": "Shell command to execute via SSH",
      "risk_level": "safe|moderate|high"
    }}
  ],
  "manual_intervention_needed": true/false,
  "escalation_reason": "Why manual intervention is needed (if applicable)"
}}"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = message.content[0].text.strip()
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            diagnosis = json.loads(response_text)
            logging.info(f"Claude diagnosis: {diagnosis['diagnosis']}")
            return diagnosis

        except Exception as e:
            logging.error(f"Claude diagnosis failed: {e}")
            return None

    def execute_auto_repair(self, diagnosis):
        """Execute automatic repair actions if safe"""

        if not diagnosis or not diagnosis.get("auto_repair_safe"):
            logging.info("Auto-repair not safe, skipping")
            return False

        repair_results = []

        for action in diagnosis.get("repair_actions", []):
            if action.get("risk_level") in ["safe", "moderate"]:
                try:
                    logging.info(f"Executing repair: {action['description']}")

                    # Execute command via SSH
                    result = subprocess.run(
                        ['ssh', f'root@{SERVER_HOST}', action["command"]],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    repair_results.append({
                        "action": action["description"],
                        "success": result.returncode == 0,
                        "output": result.stdout,
                        "error": result.stderr
                    })

                    logging.info(f"Repair completed: {action['description']} - Success: {result.returncode == 0}")

                except Exception as e:
                    logging.error(f"Repair failed: {action['description']} - {e}")
                    repair_results.append({
                        "action": action["description"],
                        "success": False,
                        "error": str(e)
                    })

        return repair_results

    def send_to_n8n(self, report_type, data):
        """Send bug reports or alerts to N8N workflow"""

        if not N8N_WEBHOOK_URL:
            logging.warning("N8N webhook URL not configured")
            return

        payload = {
            "timestamp": datetime.now().isoformat(),
            "type": report_type,
            "data": data,
            "source": "monitoring-agent"
        }

        try:
            response = requests.post(
                N8N_WEBHOOK_URL,
                json=payload,
                timeout=10
            )
            logging.info(f"Sent {report_type} to N8N: {response.status_code}")
        except Exception as e:
            logging.error(f"Failed to send to N8N: {e}")

    def run_monitoring_cycle(self):
        """Execute one complete monitoring cycle"""

        logging.info("=== Starting monitoring cycle ===")

        # 1. Check health
        health_report = self.check_application_health()

        # 2. If errors detected, diagnose with Claude
        if health_report["errors"]:
            logging.warning(f"Detected {len(health_report['errors'])} issues")

            diagnosis = self.diagnose_with_claude(health_report)

            if diagnosis:
                # 3. If critical, attempt auto-repair
                if diagnosis["severity"] in ["critical", "high"] and diagnosis["auto_repair_safe"]:
                    logging.info("Attempting auto-repair...")
                    repair_results = self.execute_auto_repair(diagnosis)

                    # Send repair report to N8N
                    self.send_to_n8n("auto_repair", {
                        "health_report": health_report,
                        "diagnosis": diagnosis,
                        "repair_results": repair_results
                    })

                # 4. If manual intervention needed, create N8N bug report
                if diagnosis.get("manual_intervention_needed"):
                    logging.warning("Manual intervention required, creating bug report")
                    self.send_to_n8n("bug_report", {
                        "health_report": health_report,
                        "diagnosis": diagnosis,
                        "priority": diagnosis["severity"]
                    })
        else:
            logging.info("All systems healthy")

        logging.info("=== Monitoring cycle complete ===")
        return health_report

def main():
    """Main monitoring loop"""
    agent = MonitoringAgent()

    logging.info("Monitoring Agent started")
    print("Monitoring Agent started - logging to /var/log/monitoring-agent.log")

    # Run monitoring every 5 minutes
    while True:
        try:
            agent.run_monitoring_cycle()
        except Exception as e:
            logging.error(f"Monitoring cycle failed: {e}")

        # Wait 5 minutes before next check
        time.sleep(300)

if __name__ == "__main__":
    main()
