from __future__ import annotations

import calendar
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class MolitBackfillTask:
    provider_dataset: str
    fact_type: str
    lawd_code: str
    deal_ym: str

    @property
    def run_key(self) -> str:
        return f"{self.provider_dataset}:{self.lawd_code}:{self.deal_ym}"

    def to_payload(self) -> dict:
        year = int(self.deal_ym[:4])
        month = int(self.deal_ym[4:])
        requested_from = date(year, month, 1)
        requested_to = date(year, month, calendar.monthrange(year, month)[1])
        return {
            "runKey": self.run_key,
            "provider": "molit",
            "providerDataset": self.provider_dataset,
            "factType": self.fact_type,
            "lawdCode": self.lawd_code,
            "dealYm": self.deal_ym,
            "requestedFrom": requested_from.isoformat(),
            "requestedTo": requested_to.isoformat(),
            "requestParams": {
                "LAWD_CD": self.lawd_code,
                "DEAL_YMD": self.deal_ym,
            },
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "MolitBackfillTask":
        provider = str(payload.get("provider", "molit")).strip().lower()
        if provider != "molit":
            raise ValueError(f"unsupported backfill provider: {provider}")

        request_params = payload.get("requestParams") or {}
        lawd_code = _normalize_lawd_code(str(payload.get("lawdCode") or request_params.get("LAWD_CD") or ""))
        deal_ym = _parse_ym(str(payload.get("dealYm") or request_params.get("DEAL_YMD") or ""))
        provider_dataset = str(payload.get("providerDataset", "")).strip()
        normalized_dataset, fact_type = _dataset_contract(provider_dataset)
        payload_fact_type = str(payload.get("factType") or fact_type).strip()
        if payload_fact_type != fact_type:
            raise ValueError(f"factType does not match providerDataset: {payload_fact_type} != {fact_type}")
        task = cls(
            provider_dataset=normalized_dataset,
            fact_type=fact_type,
            lawd_code=lawd_code,
            deal_ym=deal_ym,
        )
        payload_run_key = str(payload.get("runKey") or task.run_key).strip()
        if payload_run_key != task.run_key:
            raise ValueError(f"runKey does not match task fields: {payload_run_key} != {task.run_key}")
        return task


@dataclass(frozen=True)
class MolitBackfillChunk:
    chunk_index: int
    tasks: tuple[MolitBackfillTask, ...]

    @property
    def chunk_key(self) -> str:
        return f"molit_backfill_chunk:{self.chunk_index:06d}"

    def to_payload(self) -> dict:
        return {
            "chunkIndex": self.chunk_index,
            "chunkKey": self.chunk_key,
            "runCount": len(self.tasks),
            "firstRunKey": self.tasks[0].run_key if self.tasks else None,
            "lastRunKey": self.tasks[-1].run_key if self.tasks else None,
            "items": [task.to_payload() for task in self.tasks],
        }


def build_molit_backfill_plan(
    *,
    lawd_codes: list[str],
    start_ym: str,
    end_ym: str,
    datasets: list[str],
) -> list[MolitBackfillTask]:
    normalized_start = _parse_ym(start_ym)
    normalized_end = _parse_ym(end_ym)
    if normalized_start > normalized_end:
        raise ValueError("start_ym must be before or equal to end_ym")

    normalized_lawd_codes = [_normalize_lawd_code(code) for code in lawd_codes]
    normalized_datasets = [_dataset_contract(dataset) for dataset in datasets]
    tasks: list[MolitBackfillTask] = []
    for deal_ym in _month_range(normalized_start, normalized_end):
        for lawd_code in normalized_lawd_codes:
            for provider_dataset, fact_type in normalized_datasets:
                tasks.append(
                    MolitBackfillTask(
                        provider_dataset=provider_dataset,
                        fact_type=fact_type,
                        lawd_code=lawd_code,
                        deal_ym=deal_ym,
                    )
                )
    return tasks


def chunk_molit_backfill_plan(
    tasks: list[MolitBackfillTask],
    *,
    chunk_size: int,
) -> list[MolitBackfillChunk]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")
    chunks: list[MolitBackfillChunk] = []
    for start_index in range(0, len(tasks), chunk_size):
        chunks.append(
            MolitBackfillChunk(
                chunk_index=len(chunks) + 1,
                tasks=tuple(tasks[start_index:start_index + chunk_size]),
            )
        )
    return chunks


def build_molit_backfill_plan_from_data_targets(
    data_targets: list[dict],
    *,
    start_ym: str,
    end_ym: str,
) -> list[MolitBackfillTask]:
    normalized_start = _parse_ym(start_ym)
    normalized_end = _parse_ym(end_ym)
    if normalized_start > normalized_end:
        raise ValueError("start_ym must be before or equal to end_ym")

    target_pairs: set[tuple[str, str]] = set()
    for target in data_targets:
        if target.get("enabled") is False:
            continue
        if str(target.get("provider", "")).strip().lower() != "molit":
            continue
        lawd_code = str(target.get("lawdCode", "")).strip()
        if not lawd_code:
            continue
        provider_dataset = str(target.get("providerDataset", "")).strip()
        try:
            normalized_lawd_code = _normalize_lawd_code(lawd_code)
            dataset_contract = _dataset_contract(provider_dataset)
        except ValueError:
            continue
        target_pairs.add((normalized_lawd_code, dataset_contract[0]))

    tasks: list[MolitBackfillTask] = []
    for deal_ym in _month_range(normalized_start, normalized_end):
        for lawd_code, provider_dataset in sorted(target_pairs, key=lambda pair: (pair[0], _dataset_sort_rank(pair[1]))):
            fact_type = _fact_type_from_provider_dataset(provider_dataset)
            tasks.append(
                MolitBackfillTask(
                    provider_dataset=provider_dataset,
                    fact_type=fact_type,
                    lawd_code=lawd_code,
                    deal_ym=deal_ym,
                )
            )
    return tasks


def load_molit_backfill_plan_manifest(path: str | Path) -> list[MolitBackfillTask]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    items = payload.get("items")
    if items is None and isinstance(payload.get("chunks"), list):
        items = [
            item
            for chunk in payload["chunks"]
            if isinstance(chunk, dict)
            for item in chunk.get("items", [])
        ]
    if not isinstance(items, list):
        raise ValueError("backfill plan manifest must contain an items list")

    tasks = [MolitBackfillTask.from_payload(item) for item in items]
    seen_run_keys: set[str] = set()
    deduped_tasks: list[MolitBackfillTask] = []
    for task in tasks:
        if task.run_key in seen_run_keys:
            continue
        seen_run_keys.add(task.run_key)
        deduped_tasks.append(task)
    return deduped_tasks


def _month_range(start_ym: str, end_ym: str) -> list[str]:
    start_year = int(start_ym[:4])
    start_month = int(start_ym[4:])
    end_year = int(end_ym[:4])
    end_month = int(end_ym[4:])
    months: list[str] = []
    year = start_year
    month = start_month
    while (year, month) <= (end_year, end_month):
        months.append(f"{year:04d}{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return months


def _parse_ym(value: str) -> str:
    if not re.fullmatch(r"\d{6}", value):
        raise ValueError("year-month must be YYYYMM")
    year = int(value[:4])
    month = int(value[4:])
    if month < 1 or month > 12:
        raise ValueError("year-month must have a month between 01 and 12")
    return f"{year:04d}{month:02d}"


def _normalize_lawd_code(value: str) -> str:
    normalized = value.strip()
    if not re.fullmatch(r"\d{5}", normalized):
        raise ValueError("lawd_code must be a 5 digit legal-dong prefix")
    return normalized


def _dataset_contract(value: str) -> tuple[str, str]:
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"trade", "apt-trade", "molit-apt-trade"}:
        return ("molit_apt_trade", "apt_trade")
    if normalized in {"rent", "apt-rent", "molit-apt-rent", "lease"}:
        return ("molit_apt_rent", "apt_rent")
    raise ValueError(f"unsupported MOLIT backfill dataset: {value}")


def _fact_type_from_provider_dataset(provider_dataset: str) -> str:
    if provider_dataset == "molit_apt_trade":
        return "apt_trade"
    if provider_dataset == "molit_apt_rent":
        return "apt_rent"
    raise ValueError(f"unsupported MOLIT provider dataset: {provider_dataset}")


def _dataset_sort_rank(provider_dataset: str) -> int:
    if provider_dataset == "molit_apt_trade":
        return 0
    if provider_dataset == "molit_apt_rent":
        return 1
    return 99
