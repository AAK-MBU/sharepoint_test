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

    sharepoint_site_url = 'https://aarhuskommune.sharepoint.com'
    modersmaal_sharepoint_site_url = 'https://aarhuskommune.sharepoint.com/teams/Teams-Modersmlsundervisning'
    mbu_rpa_sharepoint_site_url = "https://aarhuskommune.sharepoint.com/teams/MBURPA"

    tenant = os.getenv("TENANT")
    client_id = os.getenv("CLIENT_ID")
    thumbprint = os.getenv("APPREG_THUMBPRINT")
    cert_path = os.getenv("GRAPH_CERT_PEM")

    print(f"tenant: {tenant}")
    print(f"client_id: {client_id}")
    print(f"thumbprint: {thumbprint}")
    print(f"cert_path: {cert_path}")

    sp = Sharepoint(
        tenant=tenant,
        client_id=client_id,
        thumbprint=thumbprint,
        cert_path=cert_path,
        site_url="https://aarhuskommune.sharepoint.com",
        site_name="MBURPA",
        document_library="Delte dokumenter"   # or whatever your library is called
    )

    files = sp.fetch_files_list("Automation_Server")
    print(files)

    sys.exit(0)
