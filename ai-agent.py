# Task 5: AI-powered Kubernetes troubleshooting agent using Gemini AI

import os
import subprocess
from google import genai

# Collect kubectl logs for a pod
def get_logs(pod_name, namespace="retail"):
    result = subprocess.run(
        ["kubectl", "logs", pod_name, "-n", namespace, "--tail=100"],
        capture_output=True, text=True
    )
    return result.stdout

# Collect pod events and status details
def get_events(pod_name, namespace="retail"):
    result = subprocess.run(
        ["kubectl", "describe", "pod", pod_name, "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout

# Get all pods in namespace
def get_pods(namespace="retail"):
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout

# Get recent K8s events sorted by time
def get_k8s_events(namespace="retail"):
    result = subprocess.run(
        ["kubectl", "get", "events", "-n", namespace, "--sort-by=.lastTimestamp"],
        capture_output=True, text=True
    )
    return result.stdout

# Send logs and events to Gemini for analysis
def analyze_with_gemini(logs, events, scenario):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please get a free API key from Google AI Studio (aistudio.google.com).")
    
    # Initialize the modern Google GenAI client
    client = genai.Client(api_key=api_key)
    
    prompt = (
        f"Kubernetes issue: {scenario}\n\n"
        f"Pod Logs:\n{logs}\n\n"
        f"Pod Events:\n{events}\n\n"
        "Find the root cause and provide step-by-step remediation."
    )
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text

# Scenario 1: Pod continuously restarting (CrashLoopBackOff)
def troubleshoot_pod_restart(pod_name):
    print(f"\n--- Scenario 1: Pod {pod_name} is restarting ---")
    logs = get_logs(pod_name)
    events = get_events(pod_name)
    analysis = analyze_with_gemini(logs, events, "pod is continuously restarting / CrashLoopBackOff")
    print(analysis)

# Scenario 2: High latency after deployment
def troubleshoot_high_latency(pod_name):
    print(f"\n--- Scenario 2: High latency detected for {pod_name} ---")
    logs = get_logs(pod_name)
    events = get_events(pod_name)
    analysis = analyze_with_gemini(logs, events, "application latency increased after deployment")
    print(analysis)

# Scenario 3: Deployment failed
def troubleshoot_deployment_failure(namespace="retail"):
    print(f"\n--- Scenario 3: Deployment failed in {namespace} ---")
    events = get_k8s_events(namespace)
    pods = get_pods(namespace)
    analysis = analyze_with_gemini(pods, events, "deployment failed in Kubernetes")
    print(analysis)

# Main
if __name__ == "__main__":
    # Dynamically find a running userprofile pod in the retail namespace
    try:
        pod = subprocess.run(
            ["kubectl", "get", "pods", "-n", "retail", "-l", "app=userprofile", "-o", "jsonpath={.items[0].metadata.name}"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        pod = ""

    if not pod:
        print("No active userprofile pods found in 'retail' namespace. Using fallback pod name.")
        pod = "userprofile-rollout-7c79cc995f-pzlsq"

    troubleshoot_pod_restart(pod)
    
    import time
    print("\n[Pausing for 2 seconds to avoid API rate limits...]")
    time.sleep(2)
    
    troubleshoot_high_latency(pod)
    
    print("\n[Pausing for 2 seconds to avoid API rate limits...]")
    time.sleep(2)
    
    troubleshoot_deployment_failure()
