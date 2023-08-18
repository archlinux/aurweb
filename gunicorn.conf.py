from prometheus_client import multiprocess


def child_exit(server, worker):  # pragma: no cover
    """This function is required for gunicorn customization
    of prometheus multiprocessing."""
    multiprocess.mark_process_dead(worker.pid)
