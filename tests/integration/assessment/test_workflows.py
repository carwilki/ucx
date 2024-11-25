import io
from datetime import timedelta

from databricks.sdk.errors import NotFound, InvalidParameterValue
from databricks.sdk.retries import retried
from databricks.sdk.service.iam import PermissionLevel


@retried(on=[NotFound, InvalidParameterValue], timeout=timedelta(minutes=8))
def test_running_real_assessment_job(
    ws, installation_ctx, make_cluster_policy, make_cluster_policy_permissions, make_job, make_notebook, make_dashboard
):
    ws_group, _ = installation_ctx.make_ucx_group()
    cluster_policy = make_cluster_policy()
    make_cluster_policy_permissions(
        object_id=cluster_policy.policy_id,
        permission_level=PermissionLevel.CAN_USE,
        group_name=ws_group.display_name,
    )
    installation_ctx.__dict__['include_object_permissions'] = [f"cluster-policies:{cluster_policy.policy_id}"]
    installation_ctx.workspace_installation.run()

    notebook_path = make_notebook(content=io.BytesIO(b"import xyz"))
    job = make_job(notebook_path=notebook_path)
    installation_ctx.config.include_job_ids = [job.job_id]

    dashboard = make_dashboard()
    installation_ctx.config.include_dashboard_ids = [dashboard.id]

    installation_ctx.deployed_workflows.run_workflow("assessment")
    assert installation_ctx.deployed_workflows.validate_step("assessment")

    after = installation_ctx.generic_permissions_support.load_as_dict("cluster-policies", cluster_policy.policy_id)
    assert after[ws_group.display_name] == PermissionLevel.CAN_USE
