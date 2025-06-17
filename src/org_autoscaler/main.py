from core.org_autoscaler import OrgAutoscaler

if __name__ == "__main__":
    autoscaler = OrgAutoscaler(workflow_id="sample_workflow", interval=60.0)
    autoscaler.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down autoscaler")