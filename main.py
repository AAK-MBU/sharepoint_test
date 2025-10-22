"""
This is the main entry point for the process
"""

import asyncio
import logging
import sys
import os

from automation_server_client import AutomationServer, Workqueue
from mbu_rpa_core.exceptions import BusinessError, ProcessError
from mbu_rpa_core.process_states import CompletedState

from helpers import ats_functions, config
from processes.application_handler import close, reset, startup
from processes.error_handling import ErrorContext, handle_error
from processes.finalize_process import finalize_process
from processes.process_item import process_item
from processes.queue_handler import concurrent_add, retrieve_items_for_queue

from helpers.sharepoint_class import Sharepoint


logger = logging.getLogger(__name__)


if __name__ == "__main__":
    ats_functions.init_logger()

    ats = AutomationServer.from_environment()

    prod_workqueue = ats.workqueue()
    process = ats.process

    sites = [
        {
            "site_name": "MBURPA",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/MBURPA",
        },


        {
            "site_name": "Teams-Modersmlsundervisning",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/Teams-Modersmlsundervisning",
        },


        {
            "site_name": "Personale-Saramarbejdsprojekter",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/Personale-Saramarbejdsprojekter",
        },
        {
            "site_name": "Personale-Saramarbejdsprojekter-Masseudsendelse",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/Personale-Saramarbejdsprojekter-Masseudsendelse",
        },
        {
            "site_name": "Personale-Saramarbejdsprojekter-SDLn",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/Personale-Saramarbejdsprojekter-SDLn",
        },


        {
            "site_name": "PPR-Samarbejdsprojekter",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/PPR-Samarbejdsprojekter",
        },
        {
            "site_name": "PPR-Samarbejdsprojekter-CenterforTrivsel",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/PPR-Samarbejdsprojekter-CenterforTrivsel",
        },


        {
            "site_name": "Tandplejen-Samarbejdsprojekter",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/Tandplejen-Samarbejdsprojekter",
        },
        {
            "site_name": "Tandplejen-Samarbejdsprojekter-TilflyttertilAarhusKommune",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/Tandplejen-Samarbejdsprojekter-TilflyttertilAarhusKommune",
        },
        {
            "site_name": "Tandplejen-Samarbejdsprojekter-Udskrivning22r",
            "site_url": "https://aarhuskommune.sharepoint.com/teams/Tandplejen-Samarbejdsprojekter-Udskrivning22r",
        },

    ]

    tenant = os.getenv("TENANT")
    client_id = os.getenv("CLIENT_ID")
    thumbprint = os.getenv("APPREG_THUMBPRINT")
    cert_path = os.getenv("GRAPH_CERT_PEM")

    logger.info(f"tenant: {tenant}")
    logger.info(f"client_id: {client_id}")
    logger.info(f"thumbprint: {thumbprint}")
    logger.info(f"cert_path: {cert_path}")

    for site in sites:
        logger.info(f"attempting to authenticate to {site}")

        site_name = site.get("site_name")
        site_url = "https://aarhuskommune.sharepoint.com"

        try:
            sp = Sharepoint(
                tenant=tenant,
                client_id=client_id,
                thumbprint=thumbprint,
                cert_path=cert_path,
                site_url=site_url,
                site_name=site_name,
                document_library="Delte dokumenter"
            )

        except Exception as e:
            logger.info(f"Error authenticating: {e}")
