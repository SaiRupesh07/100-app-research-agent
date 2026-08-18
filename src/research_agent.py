"""
Main research agent orchestrator.

Coordinates the research pipeline:

1. Load the 100-app dataset
2. Discover official sources for each app
3. Retrieve official evidence
4. Merge discovered evidence with existing structured research data
5. Extract structured fields
6. Classify buildability and access model
7. Identify the main blocker
8. Score confidence
9. Generate first-pass research output
10. Enable verification workflow

The existing dataset is preserved. Newly discovered official evidence
is added to the research process without fabricating unsupported values.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.config import (
    FINAL_DATASET_PATH,
    FIRST_PASS_RESEARCH_PATH,
    load_final_dataset,
    save_research_output,
)

from src.research.extraction import extract_all_fields

from src.research.classification import (
    classify_buildability,
    identify_main_blocker,
    generate_buildability_reason,
)

from src.research.confidence import (
    score_overall_confidence,
)

from src.research.source_discovery import (
    research_app_sources,
)


logger = logging.getLogger(__name__)


# ============================================================
# RESEARCH AGENT
# ============================================================

class ResearchAgent:
    """
    Orchestrates the complete research pipeline.

    Existing structured data is preserved as a baseline while
    newly discovered official sources are added to the research
    record.
    """

    def __init__(
        self,
        output_path: Path = FIRST_PASS_RESEARCH_PATH,
    ):
        """
        Initialize the research agent.

        Args:
            output_path:
                Path where first-pass research results are saved.
        """

        self.output_path = output_path

        self.apps: List[Dict[str, Any]] = []

        self.research_results: List[Dict[str, Any]] = []

        self.timestamp = datetime.now().isoformat()

    # ========================================================
    # LOAD DATASET
    # ========================================================

    def load_apps(self) -> List[Dict[str, Any]]:
        """
        Load the existing 100-app dataset.

        The original dataset is never modified by this method.
        """

        logger.info(
            "Loading apps from %s",
            FINAL_DATASET_PATH,
        )

        self.apps = load_final_dataset()

        logger.info(
            "Loaded %d apps",
            len(self.apps),
        )

        return self.apps

    # ========================================================
    # EVIDENCE HELPERS
    # ========================================================

    @staticmethod
    def _merge_evidence(
        existing_evidence: List[Dict[str, Any]],
        discovered_evidence: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge existing and newly discovered evidence.

        Deduplicates by URL + claim.

        Existing evidence is retained. Newly discovered official
        evidence is added afterward.
        """

        merged: List[Dict[str, Any]] = []

        seen = set()

        for evidence_item in (
            existing_evidence or []
        ) + (
            discovered_evidence or []
        ):

            if not isinstance(
                evidence_item,
                dict,
            ):
                continue

            url = str(
                evidence_item.get(
                    "url",
                    "",
                )
            ).strip()

            claim = str(
                evidence_item.get(
                    "claim",
                    "",
                )
            ).strip()

            key = (
                url,
                claim,
            )

            if key in seen:
                continue

            seen.add(key)

            merged.append(
                evidence_item
            )

        return merged

    @staticmethod
    def _extract_auth_from_evidence(
        evidence: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Extract authentication methods only when the evidence
        explicitly mentions them.

        This is intentionally conservative.
        """

        methods = []

        for item in evidence or []:

            claim = str(
                item.get(
                    "claim",
                    "",
                )
            ).lower()

            if "oauth" in claim:
                methods.append("OAuth2")

            if (
                "api key" in claim
                or "apikey" in claim
            ):
                methods.append("API Key")

            if "bearer token" in claim:
                methods.append(
                    "Bearer Token"
                )

            if "jwt" in claim:
                methods.append("JWT")

            if "basic auth" in claim:
                methods.append("Basic Auth")

        # Preserve order while removing duplicates.
        return list(
            dict.fromkeys(methods)
        )

    @staticmethod
    def _extract_api_types_from_evidence(
        evidence: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Extract API types only when explicitly mentioned by evidence.
        """

        api_types = []

        for item in evidence or []:

            claim = str(
                item.get(
                    "claim",
                    "",
                )
            ).lower()

            if "rest" in claim:
                api_types.append("REST")

            if "graphql" in claim:
                api_types.append(
                    "GraphQL"
                )

            if "webhook" in claim:
                api_types.append(
                    "Webhook"
                )

            if "sdk" in claim:
                api_types.append("SDK")

            if "soap" in claim:
                api_types.append("SOAP")

            if "websocket" in claim:
                api_types.append(
                    "WebSocket"
                )

            if "grpc" in claim:
                api_types.append("gRPC")

            if "cli" in claim:
                api_types.append("CLI")

        return list(
            dict.fromkeys(api_types)
        )

    @staticmethod
    def _extract_mcp_from_evidence(
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Detect MCP only when official evidence explicitly
        mentions MCP.
        """

        for item in evidence or []:

            claim = str(
                item.get(
                    "claim",
                    "",
                )
            ).lower()

            source_type = str(
                item.get(
                    "source_type",
                    "",
                )
            ).lower()

            if (
                "mcp" in claim
                and "official" in source_type
            ):

                return {
                    "available": True,
                    "type": "Official MCP",
                    "url": item.get("url"),
                }

        return {
            "available": False,
            "type": "No MCP Found",
            "url": None,
        }

    @staticmethod
    def _infer_api_breadth(
        existing_breadth: str,
        api_types: List[str],
    ) -> str:
        """
        Preserve existing API breadth unless it is unknown.

        We intentionally do not invent a breadth classification
        simply because a page mentions REST or GraphQL.
        """

        valid_values = {
            "Broad",
            "Moderate",
            "Narrow",
            "Very Narrow",
            "No Public API",
            "Unknown",
        }

        if existing_breadth in valid_values:
            return existing_breadth

        return "Unknown"

    # ========================================================
    # BUILD RESEARCH INPUT
    # ========================================================

    def _build_research_input(
        self,
        app_data: Dict[str, Any],
        source_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge existing structured research data with newly
        discovered official evidence.

        Existing values are preserved unless the new evidence
        provides a safe, explicit improvement.
        """

        research_input = dict(
            app_data
        )

        existing_evidence = app_data.get(
            "evidence",
            [],
        )

        discovered_evidence = source_result.get(
            "evidence",
            [],
        )

        merged_evidence = self._merge_evidence(
            existing_evidence,
            discovered_evidence,
        )

        research_input["evidence"] = (
            merged_evidence
        )

        # ----------------------------------------------------
        # Authentication
        # ----------------------------------------------------

        discovered_auth = (
            self._extract_auth_from_evidence(
                discovered_evidence
            )
        )

        existing_auth = app_data.get(
            "auth_methods",
            [],
        )

        if isinstance(
            existing_auth,
            str,
        ):
            existing_auth = [
                existing_auth
            ]

        if not isinstance(
            existing_auth,
            list,
        ):
            existing_auth = []

        research_input["auth_methods"] = list(
            dict.fromkeys(
                existing_auth
                + discovered_auth
            )
        )

        # ----------------------------------------------------
        # API types
        # ----------------------------------------------------

        discovered_api_types = (
            self._extract_api_types_from_evidence(
                discovered_evidence
            )
        )

        existing_api_types = app_data.get(
            "api_types",
            [],
        )

        if isinstance(
            existing_api_types,
            str,
        ):
            existing_api_types = [
                existing_api_types
            ]

        if not isinstance(
            existing_api_types,
            list,
        ):
            existing_api_types = []

        research_input["api_types"] = list(
            dict.fromkeys(
                existing_api_types
                + discovered_api_types
            )
        )

        # ----------------------------------------------------
        # MCP
        # ----------------------------------------------------

        discovered_mcp = (
            self._extract_mcp_from_evidence(
                discovered_evidence
            )
        )

        existing_mcp_available = bool(
            app_data.get(
                "mcp_available",
                False,
            )
        )

        existing_mcp_url = app_data.get(
            "mcp_url"
        )

        existing_mcp_type = app_data.get(
            "mcp_type",
            "No MCP Found",
        )

        if discovered_mcp["available"]:

            research_input[
                "mcp_available"
            ] = True

            research_input[
                "mcp_type"
            ] = discovered_mcp[
                "type"
            ]

            research_input[
                "mcp_url"
            ] = discovered_mcp[
                "url"
            ]

        else:

            research_input[
                "mcp_available"
            ] = existing_mcp_available

            research_input[
                "mcp_type"
            ] = existing_mcp_type

            research_input[
                "mcp_url"
            ] = existing_mcp_url

        # ----------------------------------------------------
        # API breadth
        # ----------------------------------------------------

        research_input["api_breadth"] = (
            self._infer_api_breadth(
                app_data.get(
                    "api_breadth",
                    "Unknown",
                ),
                research_input[
                    "api_types"
                ],
            )
        )

        # ----------------------------------------------------
        # Research status
        # ----------------------------------------------------

        source_status = source_result.get(
            "research_status",
            "unknown",
        )

        research_input[
            "source_discovery_status"
        ] = source_status

        research_input[
            "source_discovery_pages"
        ] = source_result.get(
            "retrieved_pages",
            0,
        )

        research_input[
            "source_discovery_errors"
        ] = source_result.get(
            "errors",
            [],
        )

        return research_input

    # ========================================================
    # RESEARCH ONE APP
    # ========================================================

    def research_app(
        self,
        app_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Research one app.

        Steps:

        1. Discover official sources
        2. Merge official evidence
        3. Extract structured fields
        4. Classify buildability
        5. Identify blocker
        6. Generate explanation
        7. Score confidence
        8. Return structured research record
        """

        app_name = app_data.get(
            "app_name",
            "Unknown",
        )

        logger.info(
            "Researching %s",
            app_name,
        )

        # ----------------------------------------------------
        # STEP 1 — Official source discovery
        # ----------------------------------------------------

        try:

            source_result = (
                research_app_sources(
                    app_name
                )
            )

        except Exception as exc:

            logger.exception(
                "Source discovery failed for %s",
                app_name,
            )

            source_result = {
                "app_name": app_name,
                "sources": [],
                "evidence": [],
                "retrieved_pages": 0,
                "research_status": "failed",
                "errors": [
                    str(exc)
                ],
            }

        logger.info(
            "%s: source discovery status=%s pages=%s evidence=%s",
            app_name,
            source_result.get(
                "research_status"
            ),
            source_result.get(
                "retrieved_pages",
                0,
            ),
            len(
                source_result.get(
                    "evidence",
                    [],
                )
            ),
        )

        # ----------------------------------------------------
        # STEP 2 — Merge source evidence
        # ----------------------------------------------------

        research_input = (
            self._build_research_input(
                app_data,
                source_result,
            )
        )

        # ----------------------------------------------------
        # STEP 3 — Structured extraction
        # ----------------------------------------------------

        extracted = extract_all_fields(
            research_input
        )

        # ----------------------------------------------------
        # Classification inputs
        # ----------------------------------------------------

        api_breadth = extracted.get(
            "api_breadth",
            "Unknown",
        )

        api_available = (
            api_breadth
            not in {
                "No Public API",
                "Unknown",
            }
        )

        access = extracted.get(
            "access",
            {},
        )

        self_serve = access.get(
            "self_serve"
        )

        if self_serve is None:
            self_serve = False

        auth_methods = extracted.get(
            "auth_methods",
            [],
        )

        access_model = access.get(
            "model",
            "Unknown",
        )

        evidence = extracted.get(
            "evidence",
            [],
        )

        # ----------------------------------------------------
        # STEP 4 — Initial buildability
        # ----------------------------------------------------

        initial_blocker = (
            app_data.get(
                "main_blocker"
            )
        )

        buildability = (
            classify_buildability(
                api_available=api_available,
                api_breadth=api_breadth,
                self_serve=self_serve,
                auth_methods=auth_methods,
                access_model=access_model,
                main_blocker=initial_blocker,
            )
        )

        # ----------------------------------------------------
        # STEP 5 — Main blocker
        # ----------------------------------------------------

        main_blocker = (
            identify_main_blocker(
                api_available=api_available,
                api_breadth=api_breadth,
                self_serve=self_serve,
                partner_or_contact_sales=bool(
                    access.get(
                        "partner_or_contact_sales"
                    )
                ),
                admin_approval_required=bool(
                    access.get(
                        "admin_approval_required"
                    )
                ),
                paid_plan_required=bool(
                    access.get(
                        "paid_plan_required"
                    )
                ),
                evidence=evidence,
            )
        )

        # If no newly calculated blocker exists,
        # preserve an existing documented blocker.
        if (
            main_blocker is None
            and initial_blocker
        ):
            main_blocker = initial_blocker

        # ----------------------------------------------------
        # STEP 6 — Final buildability
        # ----------------------------------------------------

        buildability = (
            classify_buildability(
                api_available=api_available,
                api_breadth=api_breadth,
                self_serve=self_serve,
                auth_methods=auth_methods,
                access_model=access_model,
                main_blocker=main_blocker,
            )
        )

        # ----------------------------------------------------
        # STEP 7 — Explanation
        # ----------------------------------------------------

        buildability_reason = (
            generate_buildability_reason(
                buildability=buildability,
                api_available=api_available,
                api_breadth=api_breadth,
                self_serve=self_serve,
                auth_methods=auth_methods,
                access_model=access_model,
                main_blocker=main_blocker,
            )
        )

        # ----------------------------------------------------
        # STEP 8 — Confidence
        # ----------------------------------------------------

        confidence = (
            score_overall_confidence(
                extracted
            )
        )

        # ----------------------------------------------------
        # STEP 9 — Final record
        # ----------------------------------------------------

        result = {
            "id": extracted.get(
                "id"
            ),

            "app_name": extracted.get(
                "app_name",
                app_name,
            ),

            "category": extracted.get(
                "category",
                app_data.get(
                    "category",
                    "",
                ),
            ),

            "description": extracted.get(
                "description",
                "",
            ),

            "auth_methods": extracted.get(
                "auth_methods",
                [],
            ),

            "credential_model": extracted.get(
                "credential_model",
                "unknown",
            ),

            "self_serve": access.get(
                "self_serve"
            ),

            "free_or_trial": access.get(
                "free_or_trial"
            ),

            "paid_plan_required": access.get(
                "paid_plan_required"
            ),

            "admin_approval_required": access.get(
                "admin_approval_required"
            ),

            "partner_or_contact_sales": access.get(
                "partner_or_contact_sales"
            ),

            "access_model": access_model,

            "api_types": extracted.get(
                "api_types",
                [],
            ),

            "api_breadth": api_breadth,

            "api_notes": extracted.get(
                "api_notes",
                "",
            ),

            "mcp_available": extracted.get(
                "mcp",
                {},
            ).get(
                "available",
                False,
            ),

            "mcp_type": extracted.get(
                "mcp",
                {},
            ).get(
                "type",
                "No MCP Found",
            ),

            "mcp_url": extracted.get(
                "mcp",
                {},
            ).get(
                "url"
            ),

            "buildability": buildability,

            "main_blocker": main_blocker,

            "buildability_reason": (
                buildability_reason
            ),

            "evidence": evidence,

            "confidence": confidence,

            "research_status": (
                source_result.get(
                    "research_status",
                    "unknown",
                )
            ),

            "source_discovery": {
                "official_base_url": (
                    source_result.get(
                        "official_base_url"
                    )
                ),
                "retrieved_pages": (
                    source_result.get(
                        "retrieved_pages",
                        0,
                    )
                ),
                "source_count": len(
                    source_result.get(
                        "sources",
                        [],
                    )
                ),
                "errors": (
                    source_result.get(
                        "errors",
                        [],
                    )
                ),
            },

            "last_checked": self.timestamp,
        }

        return result

    # ========================================================
    # RUN PIPELINE
    # ========================================================

    def run(
        self,
        limit: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Run the research pipeline.

        Args:
            limit:
                Optional number of apps to process.
                Use --limit 3 for testing.

        Returns:
            List of researched records.
        """

        if not self.apps:
            self.load_apps()

        if limit is not None:

            if limit <= 0:
                raise ValueError(
                    "limit must be greater than 0"
                )

            apps_to_process = self.apps[
                :limit
            ]

        else:

            apps_to_process = self.apps

        logger.info(
            "Starting research on %d apps",
            len(apps_to_process),
        )

        self.research_results = []

        for index, app in enumerate(
            apps_to_process,
            start=1,
        ):

            app_name = app.get(
                "app_name",
                "Unknown",
            )

            logger.info(
                "[%d/%d] Researching %s",
                index,
                len(apps_to_process),
                app_name,
            )

            try:

                result = self.research_app(
                    app
                )

                self.research_results.append(
                    result
                )

                logger.info(
                    "[%d/%d] Completed %s",
                    index,
                    len(apps_to_process),
                    app_name,
                )

            except Exception as exc:

                logger.exception(
                    "[%d/%d] Failed %s",
                    index,
                    len(apps_to_process),
                    app_name,
                )

                # Preserve the app rather than
                # crashing the complete pipeline.
                failed_record = {
                    "id": app.get("id"),
                    "app_name": app_name,
                    "category": app.get(
                        "category",
                        "",
                    ),
                    "description": app.get(
                        "description",
                        "",
                    ),
                    "evidence": [],
                    "confidence": "Unknown",
                    "buildability": (
                        "Gated / Not Practical"
                    ),
                    "main_blocker": (
                        "Research pipeline error"
                    ),
                    "buildability_reason": (
                        "Research could not be "
                        "completed for this app."
                    ),
                    "research_status": "failed",
                    "error": str(exc),
                    "last_checked": self.timestamp,
                }

                self.research_results.append(
                    failed_record
                )

        logger.info(
            "Completed research on %d apps",
            len(self.research_results),
        )

        return self.research_results

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    def save_results(self) -> None:
        """
        Save first-pass research results.
        """

        if not self.research_results:

            logger.warning(
                "No research results to save"
            )

            return

        output = {
            "metadata": {
                "timestamp": self.timestamp,
                "total_apps": len(
                    self.research_results
                ),
                "research_stage": "first_pass",
                "description": (
                    "Initial research output "
                    "using official source discovery. "
                    "Subject to human verification."
                ),
            },

            "apps": self.research_results,
        }

        logger.info(
            "Saving research results to %s",
            self.output_path,
        )

        save_research_output(
            output,
            self.output_path,
        )

        logger.info(
            "Results saved successfully"
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    def generate_stats(
        self,
    ) -> Dict[str, Any]:
        """
        Generate statistics from research results.
        """

        if not self.research_results:
            return {}

        buildability_counts: Dict[
            str,
            int,
        ] = {}

        confidence_counts: Dict[
            str,
            int,
        ] = {}

        category_counts: Dict[
            str,
            int,
        ] = {}

        research_status_counts: Dict[
            str,
            int,
        ] = {}

        for app in self.research_results:

            buildability = app.get(
                "buildability",
                "Unknown",
            )

            buildability_counts[
                buildability
            ] = (
                buildability_counts.get(
                    buildability,
                    0,
                )
                + 1
            )

            confidence = app.get(
                "confidence",
                "Unknown",
            )

            confidence_counts[
                confidence
            ] = (
                confidence_counts.get(
                    confidence,
                    0,
                )
                + 1
            )

            category = app.get(
                "category",
                "Unknown",
            )

            category_counts[
                category
            ] = (
                category_counts.get(
                    category,
                    0,
                )
                + 1
            )

            status = app.get(
                "research_status",
                "unknown",
            )

            research_status_counts[
                status
            ] = (
                research_status_counts.get(
                    status,
                    0,
                )
                + 1
            )

        mcp_available = sum(
            1
            for app in self.research_results
            if app.get(
                "mcp_available",
                False,
            )
        )

        self_serve = sum(
            1
            for app in self.research_results
            if app.get(
                "self_serve",
                False,
            )
        )

        official_evidence_apps = sum(
            1
            for app in self.research_results
            if any(
                str(
                    item.get(
                        "source_type",
                        "",
                    )
                ).startswith("official")
                for item in app.get(
                    "evidence",
                    [],
                )
            )
        )

        total_evidence = sum(
            len(
                app.get(
                    "evidence",
                    [],
                )
            )
            for app in self.research_results
        )

        return {
            "total_apps": len(
                self.research_results
            ),

            "buildability": (
                buildability_counts
            ),

            "confidence": (
                confidence_counts
            ),

            "categories": (
                category_counts
            ),

            "research_status": (
                research_status_counts
            ),

            "mcp_available": (
                mcp_available
            ),

            "self_serve_apps": (
                self_serve
            ),

            "apps_with_official_evidence": (
                official_evidence_apps
            ),

            "total_evidence_records": (
                total_evidence
            ),

            "research_date": self.timestamp,
        }