import os
from urllib.parse import urlparse
import supervisely_lib as sly


my_app = sly.AppService(ignore_task_id=True)

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])

@my_app.callback("start_import")
@sly.timeit
def start_import(api: sly.Api, task_id, context, state, app_logger):
    pass


@my_app.callback("preview_remote")
@sly.timeit
def preview_remote(api: sly.Api, task_id, context, state, app_logger):
    remote_dir = state["remoteDir"]
    parts = urlparse(remote_dir)
    project_name = parts.path.rstrip("/")
    if project_name not in ["", "/"]:
        project_name = sly.fs.get_file_name(project_name) # last directory name from path
    else:
        project_name = ""
    fields = [{"field": "state.projectName", "payload": project_name}, ]
    api.app.set_fields(task_id, fields)


@my_app.callback("preprocessing")
@sly.timeit
def preprocessing(api: sly.Api, task_id, context, state, app_logger):
    pass


def main():
    sly.logger.info("Script arguments from modal dialog box",  extra={})

    api = sly.Api.from_env()
    team = api.team.get_info_by_id(TEAM_ID)
    workspace = api.workspace.get_info_by_id(WORKSPACE_ID)

    data = {
        "uploadStarted": False,
        "uploadedCount": 0,
        "totalCount": 0,
        "uploadProgress": 0,
        "uploadError": ""
    }

    state = {
        "remoteDir": "http://localhost:8088/my_sly_project/",
        "teamName": team.name,
        "workspaceName": workspace.name,
        "projectName": ""
    }

    # Run application service
    my_app.run(data=data, state=state)

#@TODO: remoteDir  - remove debug server
if __name__ == "__main__":
    sly.main_wrapper("main", main)