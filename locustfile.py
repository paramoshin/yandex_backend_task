"""Locustfile for load testing."""
from __future__ import annotations

import logging
from http import HTTPStatus
from typing import *

from ecommerce_analyzer.api.application import app
from locust import HttpUser, TaskSet, constant, task
from locust.exception import RescheduleTask
from requests import Response

from tests.utils import generate_citizen, generate_citizens


class AnalyzerTaskSet(TaskSet):
    """Class that describes testing workflow."""

    def __init__(self: AnalyzerTaskSet, *args: Any, **kwargs: Any) -> None:
        """Initialize instance."""
        super().__init__(*args, **kwargs)
        self.round = 0

    @staticmethod
    def make_dataset() -> dict:
        """Create max sized import dataset."""
        citizens = [
            # Первого жителя создаем с родственником. В запросе к
            # PATCH-обработчику список relatives будет содержать только другого
            # жителя, что потребует выполнения максимального кол-ва запросов
            # (как на добавление новой родственной связи, так и на удаление
            # существующей).
            generate_citizen(citizen_id=1, relatives=[2]),
            generate_citizen(citizen_id=2, relatives=[1]),
            *generate_citizens(citizens_num=9998, relations_num=1000, start_citizen_id=3),
        ]
        return {citizen["citizen_id"]: citizen for citizen in citizens}

    def request(
        self: AnalyzerTaskSet, method: str, path: str, expected_status: HTTPStatus.value, **kwargs: Any
    ) -> Response:
        """Make request."""
        with self.client.request(method, path, catch_response=True, **kwargs) as resp:
            if resp.status_code != expected_status:
                resp.failure(f"expected status {expected_status}, got {resp.status_code}")
            logging.info(
                "round %r: %s %s, http status %d (expected %d), took %rs",
                self.round,
                method,
                path,
                resp.status_code,
                expected_status,
                resp.elapsed.total_seconds(),
            )
            return resp

    def create_import(self: AnalyzerTaskSet, dataset: dict) -> int:
        """Make request to save import dataset."""
        resp = self.request("POST", "/imports", HTTPStatus.CREATED, json={"data": list(dataset.values())})
        if resp.status_code != HTTPStatus.CREATED:
            raise RescheduleTask
        return resp.json()["data"]["import_id"]

    def get_citizens(self: AnalyzerTaskSet, import_id: int) -> None:
        """Make request to get citizens."""
        url = app.router.url_path_for("get_citizens", import_id=import_id)
        self.request("GET", url, HTTPStatus.OK, name="/imports/{import_id}/citizens")

    def update_citizen(self: AnalyzerTaskSet, import_id: int) -> None:
        """Make request to patch citizen."""
        url = app.router.url_path_for("patch_citizen", import_id=import_id, citizen_id=1)
        self.request(
            "PATCH",
            url,
            HTTPStatus.OK,
            name="/imports/{import_id}/citizens/{citizen_id}",
            json={"relatives": [i for i in range(3, 10)]},
        )

    def get_birthdays(self: AnalyzerTaskSet, import_id: int) -> None:
        """Make request to get birthdays statistics."""
        url = app.router.url_path_for("get_number_of_birthdays", import_id=import_id)
        self.request("GET", url, HTTPStatus.OK, name="/imports/{import_id}/citizens/birthdays")

    def get_town_stats(self: AnalyzerTaskSet, import_id: int) -> None:
        """Make request to get age statistics."""
        url = app.router.url_path_for("get_age_statistics", import_id=import_id)
        self.request("GET", url, HTTPStatus.OK, name="/imports/{import_id}/towns/stat/percentile/age")

    @task
    def workflow(self: AnalyzerTaskSet) -> None:
        """Make requests in required sequence."""
        self.round += 1
        dataset = self.make_dataset()

        import_id = self.create_import(dataset)
        self.get_citizens(import_id)
        self.update_citizen(import_id)
        self.get_birthdays(import_id)
        self.get_town_stats(import_id)


class WebsiteUser(HttpUser):
    """Represents HTTP user, that will spawn and make requests."""

    tasks = [AnalyzerTaskSet]
    wait_time = constant(1)
