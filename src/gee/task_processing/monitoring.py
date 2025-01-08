
import asyncio
import logging
import time


logging.basicConfig(level=logging.INFO)


async def monitor_tasks(tasks, job_id):
    check_minutes = [30, 60, 90]
    start_time = time.time()

    for check_point in check_minutes:
        # Wait until next check point
        wait_time = (check_point * 60) - (time.time() - start_time)
        if wait_time > 0:
            await asyncio.sleep(wait_time)

        logging.info(
            f"Job {job_id}: Checking status after {check_point} minutes")

        # non-final tasks
        all_done = True
        for task in tasks:
            status = task.status()['state']
            if status not in ['COMPLETED', 'FAILED', 'CANCELLED']:
                all_done = False
                # Cancel if it's our last check
                if check_point == check_minutes[-1]:
                    logging.info(
                        f"Job {job_id}: Cancelling task {task.id} due to timeout")
                    task.cancel()

        if all_done:
            logging.info(f"Job {job_id}: All tasks completed")
            return
