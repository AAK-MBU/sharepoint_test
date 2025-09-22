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

from mbu_dev_shared_components.msoffice365.sharepoint_api.files import Sharepoint

from office365.sharepoint.client_context import ClientContext


site_url = 'https://aarhuskommune.sharepoint.com'
modersmaal_site_url = 'https://aarhuskommune.sharepoint.com/teams/Teams-Modersmlsundervisning'

cert_settings = {
    'client_id': os.getenv("CLIENT_ID"),
    'thumbprint': os.getenv("APPREG_THUMBPRINT"),
    'cert_path': os.getenv("GRAPH_CERT_PUBLIC")
}

ctx = ClientContext(site_url).with_client_certificate('contoso.onmicrosoft.com', **cert_settings)

current_web = ctx.web
ctx.load(current_web)
ctx.execute_query()
print("{0}".format(current_web.url))



sys.exit()



async def populate_queue(workqueue: Workqueue):
    """Populate the workqueue with items to be processed."""

    logger = logging.getLogger(__name__)
    logger.info("Populating workqueue...")

    items_to_queue = retrieve_items_for_queue(logger=logger)

    queue_references = {str(r) for r in ats_functions.get_workqueue_items(workqueue)}

    new_items: list[dict] = []
    for item in items_to_queue:
        reference = str(item.get("reference") or "")
        if reference and reference in queue_references:
            logger.info(
                f"Reference: {reference} already in queue. Item: {item} not added"
            )
        else:
            new_items.append(item)

    await concurrent_add(workqueue, new_items, logger)
    logger.info("Finished populating workqueue.")


async def process_workqueue(workqueue: Workqueue):
    """Process items from the workqueue."""

    logger = logging.getLogger(__name__)
    logger.info("Processing workqueue...")

    startup(logger=logger)

    error_count = 0

    while error_count < config.MAX_RETRY:
        for item in workqueue:
            try:
                with item:
                    data, reference = ats_functions.get_item_info(item)

                    try:
                        logger.info(f"Processing item with reference: {reference}")
                        process_item(data, reference)

                        completed_state = CompletedState.completed(
                            "Process completed without exceptions"
                        )
                        item.complete(str(completed_state))

                        continue

                    except BusinessError as e:
                        context = ErrorContext(
                            item=item,
                            action=item.pending_user,
                            send_mail=False,
                            process_name=workqueue.name,
                        )
                        handle_error(
                            error=e,
                            log=logger.info,
                            context=context,
                        )

                    except Exception as e:
                        pe = ProcessError(str(e))
                        raise pe from e

            except ProcessError as e:
                context = ErrorContext(
                    item=item,
                    action=item.fail,
                    send_mail=True,
                    process_name=workqueue.name,
                )
                handle_error(
                    error=e,
                    log=logger.error,
                    context=context,
                )
                error_count += 1
                reset(logger=logger)

    logger.info("Finished processing workqueue.")
    close(logger=logger)


async def finalize(workqueue: Workqueue):
    """Finalize process."""

    logger = logging.getLogger(__name__)

    logger.info("Finalizing process...")

    try:
        finalize_process()
        logger.info("Finished finalizing process.")

    except BusinessError as e:
        handle_error(error=e, log=logger.info)

    except Exception as e:
        pe = ProcessError(str(e))
        context = ErrorContext(
            send_mail=True,
            process_name=workqueue.name,
        )
        handle_error(error=pe, log=logger.error, context=context)

        raise pe from e


if __name__ == "__main__":
    ats_functions.init_logger()

    ats = AutomationServer.from_environment()

    prod_workqueue = ats.workqueue()
    process = ats.process

    if "--queue" in sys.argv:
        asyncio.run(populate_queue(prod_workqueue))

    if "--process" in sys.argv:
        asyncio.run(process_workqueue(prod_workqueue))

    if "--finalize" in sys.argv:
        asyncio.run(finalize(prod_workqueue))

    sys.exit(0)
