import os
import time
from functools import reduce
from urllib.parse import urljoin, urlparse

import htmllistparse
import requests
import supervisely as sly
from dotenv import load_dotenv
from slugify import slugify
from supervisely.app.v1.app_service import AppService

from src.workflow import Workflow

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

my_app: AppService = AppService(ignore_task_id=True)

TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])

listing = []


@my_app.callback("preview_remote")
@sly.timeit
def preview_remote(api: sly.Api, task_id, context, state, app_logger):
    global listing
    api.task.set_field(task_id, "data.previewError", "")
    try:
        sly.logger.debug("State in preview_remote: {}".format(state))
        remote_dir = state["remoteDir"]
        parts = urlparse(remote_dir)
        project_name = parts.path.rstrip("/")
        if project_name not in ["", "/"]:
            project_name = sly.fs.get_file_name(project_name)  # last directory name from path
        else:
            project_name = ""

        cwd, raw_listing = htmllistparse.fetch_listing(remote_dir, timeout=30)
        sly.logger.debug("Raw listing in preview_remote: {}".format(raw_listing))

        listing = []
        listing_flags = []
        meta_json_exists = False
        for file_entry in raw_listing:
            name = file_entry.name
            # name = slugify(name, lowercase=False, save_order=True)
            if name == "meta.json":
                meta_json_exists = True
                listing.append({"name": name})
                listing_flags.append({"selected": True, "disabled": True})
            elif name.endswith("/"):
                listing.append({"name": name.rstrip("/")})
                listing_flags.append({"selected": True, "disabled": False})
            else:
                app_logger.info("Skip file {!r}".format(urljoin(remote_dir, name)))
                listing.append({"name": name})
                listing_flags.append({"selected": False, "disabled": True})

        if meta_json_exists is False:
            raise FileNotFoundError("meta.json")

        fields = [
            # {"field": "state.projectName", "payload": slugify(project_name, lowercase=False, save_order=True)},
            {"field": "state.projectName", "payload": project_name},
            {"field": "data.listing", "payload": listing},
            {"field": "state.listingFlags", "payload": listing_flags},
        ]
        api.app.set_fields(task_id, fields)
    except Exception as e:
        api.task.set_field(task_id, "data.previewError", repr(e))


def _set_selected(listing_flags, flag):
    new_flags = []
    for selector in listing_flags:
        if selector["disabled"] is False:
            selector["selected"] = flag
        new_flags.append(selector)
    return new_flags


@my_app.callback("select_all")
@sly.timeit
def select_all(api: sly.Api, task_id, context, state, app_logger):
    listing_flags = state["listingFlags"]
    new_flags = _set_selected(listing_flags, True)
    if len(new_flags) > 0:
        api.task.set_field(task_id, "state.listingFlags", new_flags)


@my_app.callback("deselect_all")
@sly.timeit
def deselect_all(api: sly.Api, task_id, context, state, app_logger):
    listing_flags = state["listingFlags"]
    new_flags = _set_selected(listing_flags, False)
    if len(new_flags) > 0:
        api.task.set_field(task_id, "state.listingFlags", new_flags)


def _show_error(api, task_id, field, error, app_logger):
    app_logger.warn(error)
    fields = [
        {"field": field, "payload": error},
        {"field": "data.uploadStarted", "payload": False},
    ]
    api.app.set_fields(task_id, fields)


def _increment_ds_progress(task_id, api, current, total):
    fields = [
        {"field": "data.uploadedDsCount", "payload": current},
        {"field": "data.uploadDsProgress", "payload": int(current * 100 / total)},
    ]
    api.app.set_fields(task_id, fields)


def _increment_task_progress(task_id, api: sly.Api, sly_progress: sly.Progress):
    fields = [
        {"field": "data.uploadedCount", "payload": sly_progress.current},
        {
            "field": "data.uploadProgress",
            "payload": int(sly_progress.current * 100 / sly_progress.total),
        },
    ]
    api.app.set_fields(task_id, fields)
    pass


@my_app.callback("start_import")
@sly.timeit
def start_import(api: sly.Api, task_id, context, state, app_logger):
    sly.logger.debug("State in start_import: {}".format(state))
    fields = [
        {"field": "data.destinationError", "payload": ""},
        {"field": "data.uploadError", "payload": ""},
        {"field": "data.uploadStarted", "payload": True},
        {"field": "data.uploadedCount", "payload": 0},
        {"field": "data.totalCount", "payload": 0},
        {"field": "data.uploadProgress", "payload": 0},
        {"field": "data.uploadDsName", "payload": ""},
        {"field": "data.uploadedDsCount", "payload": 0},
        {"field": "data.totalDsCount", "payload": 0},
        {"field": "data.uploadDsProgress", "payload": 0},
    ]
    api.app.set_fields(task_id, fields)

    remote_dir = state["remoteDir"]
    listing_flags = state["listingFlags"]

    workspace_name = state["workspaceName"]
    project_name = state[
        "projectName"
    ]  # slugify(state["projectName"], lowercase=False, save_order=True)
    if project_name == "":
        _show_error(
            api,
            task_id,
            "data.destinationError",
            "Project name is not defined",
            app_logger,
        )
        return

    # @TODO: will be added in future releases
    add_to_existing_project = False  # state["addToExisting"]

    existing_meta = None
    try:
        workspace = api.workspace.get_info_by_name(TEAM_ID, workspace_name)
        if workspace is None:
            workspace = api.workspace.create(TEAM_ID, workspace_name)
            app_logger.info("Workspace {!r} is created".format(workspace.name))
        else:
            app_logger.info("Workspace {!r} already exists".format(workspace.name))

        project = api.project.get_info_by_name(workspace.id, project_name)
        if project is None:
            project = api.project.create(workspace.id, project_name)
            app_logger.info("Project {!r} is created".format(project.name))
        else:
            _show_error(
                api,
                task_id,
                "data.destinationError",
                "Project {!r} already exists".format(project.name),
                app_logger,
            )
            return

            if add_to_existing_project is False:
                app_logger.warn(
                    "Project {!r} already exists. Allow add to existing project or change the name of "
                    "destination project. We recommend to upload to new project. Thus the existing project "
                    "will be safe. New name will be generated".format(project.name)
                )
                project = api.project.create(
                    workspace.id, project_name, change_name_if_conflict=True
                )
            else:
                existing_meta_json = api.project.get_meta(project.id)
                existing_meta = sly.ProjectMeta.from_json(existing_meta_json)

        update_res_project_icon = None
        fields = [
            {"field": "data.resultProject", "payload": project.name},
            {"field": "data.resultProjectId", "payload": project.id},
            # {"field": "data.resultProjectPreviewUrl", "payload": 0},
        ]
        api.app.set_fields(task_id, fields)

        resp = requests.get(urljoin(remote_dir, "meta.json"))
        meta_json = resp.json()
        meta = sly.ProjectMeta.from_json(meta_json)
        if existing_meta is not None:
            meta = existing_meta.merge(meta)

        api.project.update_meta(project.id, meta.to_json())

        datasets_to_upload = []
        for ds_info, flags in zip(listing, listing_flags):
            dataset_name = ds_info["name"]
            if flags["selected"] is False:
                app_logger.info(
                    "Folder {!r} is not selected, it will be skipped".format(dataset_name)
                )
                continue
            if flags["disabled"] is True:
                app_logger.info("File {!r} is skipped".format(dataset_name))
                continue
            datasets_to_upload.append(dataset_name)

        api.task.set_field(task_id, "data.totalDsCount", len(datasets_to_upload))
        for index, dataset_name in enumerate(datasets_to_upload):
            dataset = api.dataset.get_info_by_name(project.id, dataset_name)
            if dataset is None:
                dataset = api.dataset.create(project.id, dataset_name)
                app_logger.info("Dataset {!r} is created".format(dataset.name))
            else:
                app_logger.warn(
                    "Dataset {!r} already exists. Uploading is skipped".format(dataset.name)
                )
                _increment_ds_progress(task_id, api, index + 1, len(datasets_to_upload))
                continue

            # img_dir = reduce(urljoin, [remote_dir, dataset_name, 'img'])
            # ann_dir = reduce(urljoin, [remote_dir, dataset_name, 'ann'])
            img_dir = os.path.join(remote_dir, dataset_name, "img/")
            ann_dir = os.path.join(remote_dir, dataset_name, "ann/")

            cwd, img_listing = htmllistparse.fetch_listing(img_dir, timeout=30)
            sly.logger.debug("Image listing in start_import: {}".format(img_listing))

            uploaded_to_dataset = 0
            fields = [
                {"field": "data.totalCount", "payload": len(img_listing)},
                {"field": "data.uploadDsName", "payload": dataset.name},
            ]
            api.app.set_fields(task_id, fields)

            task_progress = sly.Progress(
                "Uploading dataset {!r}".format(dataset.name), len(img_listing)
            )
            for batch in sly.batched(img_listing, batch_size=50):
                try:
                    names = []
                    image_urls_batch = []
                    annotations_batch = []

                    for file_entry in batch:
                        name = file_entry.name
                        try:
                            img_url = urljoin(img_dir, name)  # 'https://i.imgur.com/uFYNj9Z.jpg'
                            ann_url = urljoin(ann_dir, name + sly.ANN_EXT)

                            resp = requests.get(ann_url)
                            if resp.status_code == 404:
                                ann_url = urljoin(ann_dir, sly.fs.get_file_name(name) + sly.ANN_EXT)
                                resp = requests.get(ann_url)

                            resp.raise_for_status()
                            ann_json = resp.json()

                            ann = sly.Annotation.from_json(ann_json, meta)
                        except Exception as e:
                            app_logger.warn(
                                "Image {!r} and annotation {!r} are skipped due to error: {}".format(
                                    img_url, ann_url, repr(e)
                                )
                            )
                            continue

                        names.append(name)
                        image_urls_batch.append(img_url)
                        annotations_batch.append(ann)

                    img_infos = api.image.upload_links(dataset.id, names, image_urls_batch)
                    uploaded_ids = [img_info.id for img_info in img_infos]
                    api.annotation.upload_anns(uploaded_ids, annotations_batch)
                    uploaded_to_dataset += len(uploaded_ids)
                except Exception as e:
                    app_logger.warn(
                        "Batch ({} items) of images is skipped due to error: {}".format(
                            len(batch), repr(e)
                        )
                    )
                finally:
                    task_progress.iters_done_report(len(batch))
                    _increment_task_progress(task_id, api, task_progress)

                    # only once + to check the image urls are loaded correctly
                    if update_res_project_icon is None:
                        pinfo = api.project.get_info_by_id(project.id)
                        if pinfo.reference_image_url is None:
                            raise RuntimeError(
                                "Preview image is not accessible. Check that image URLs are public."
                            )
                        update_res_project_icon = (
                            api.image.preview_url(pinfo.reference_image_url, 100, 100),
                        )
                        api.task.set_field(
                            task_id,
                            "data.resultProjectPreviewUrl",
                            update_res_project_icon,
                        )

            _increment_ds_progress(task_id, api, index + 1, len(datasets_to_upload))
            app_logger.info(
                "Dataset {!r} is uploaded: {} images with annotations".format(
                    dataset.name, uploaded_to_dataset
                )
            )

    except Exception as e:
        app_logger.error(repr(e))
        api.task.set_field(task_id, "data.uploadError", repr(e))
    # -------------------------------------- Add Workflow Output ------------------------------------- #
    workflow = Workflow(api)
    workflow.add_output(project.id)
    # ----------------------------------------------- - ---------------------------------------------- #
    api.task.set_output_project(task_id, project.id, project.name)
    my_app.stop()


def main():
    sly.logger.info("Script arguments from modal dialog box", extra={})

    api = sly.Api.from_env()
    team = api.team.get_info_by_id(TEAM_ID)
    workspace = api.workspace.get_info_by_id(WORKSPACE_ID)

    data = {
        "uploadStarted": False,
        "uploadDsName": "",
        "uploadedDsCount": 0,
        "totalDsCount": 0,
        "uploadedCount": 0,
        "totalCount": 0,
        "uploadDsProgress": 0,
        "uploadProgress": 0,
        "uploadError": "",
        "taskId": my_app.task_id,
        "previewError": "",
        "listing": [],
        "destinationError": "",
        "resultProject": "",
        "resultProjectId": 0,
        "resultProjectPreviewUrl": "",
    }

    state = {
        # "remoteDir": "http://localhost:8088/my_sly_project/",
        # "remoteDir": "http://172.20.10.2:8088/my_sly_project/",
        "remoteDir": "",  # "http://172.17.0.1:8088/lemons_annotated_2/",
        "teamName": team.name,
        "workspaceName": workspace.name,
        "projectName": "",
        "listingFlags": [],
        "addToExisting": False,
    }

    # Run application service
    my_app.run(data=data, state=state)


# @TODO: slugify names
# @TODO: nginx volume - slow start??
if __name__ == "__main__":
    sly.main_wrapper("main", main)
