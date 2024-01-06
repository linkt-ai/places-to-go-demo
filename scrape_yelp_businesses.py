"""Scrape Yelp businesses descriptions in "scrape/searched_location_data.json" """
import json
import queue
import time
import threading
import os
from concurrent import futures


from src import launch
from src.utils import format_proxy
from src.scrape import scrape_business_reviews, scrape_business_page_content

REMAINING_FILE = "data/scrape/locations_remaining.json"
FINSIHED_FILE = "data/scrape/locations_finished.json"
FAILED_FILE = "data/scrape/locations_failed.json"
BASE_FILE = "data/scrape/locations.json"


def read_json():
    """Reads the JSON file containing the scraped data."""
    with open(REMAINING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


class IPManager:
    """Manage the IP Address Cycle"""

    def __init__(
        self,
        cluster: launch.ProxyCluster,
        warm_threshold: float = 1,
        threshold: float = 0.3,
    ) -> None:
        """Setup the IP Status object."""
        self._cluster = cluster
        self._success_rate = 1.0
        self._is_initializing = True
        self._current = 0
        self._threshold = threshold
        self._warm_threshold = warm_threshold
        self._pool_size = len(self._cluster.ips)
        self._lock = threading.Lock()

        # Has the warm pool been triggered?
        self._warm_pool_triggered = False

        # Create a condition variable for when the Reboot has been triggered
        self._reboot_condition = threading.Condition()
        self._warm_pool_condition = threading.Condition()

        self._thread_status = {i: False for i in range(self._pool_size)}

    @property
    def current(self) -> str:
        """Get the current IP and cycle the counter mod pool size"""
        with self._lock:
            thread_id = threading.get_ident()

            # Get the IP address and increment the counter MOD the pool size
            ip = self._cluster.ips[self._current]
            self._current = (self._current + 1) % self._pool_size

            # Set the thread's status to active
            self._thread_status[thread_id] = True
            return ip

    def _reboot(self):
        """Refresh the list of IPs"""
        # A thread that has entered this method owns the reboot condition
        # variable. This means that the thread will block all others from checking
        # if they need to reboot until this method has completed.

        # While there are True values in the _thread_status dictionary
        while not all(not status for status in self._thread_status.values()):
            time.sleep(1)

        # Reboot logic w/ lock just for added safety
        with self._lock:
            self._cluster.reboot()
            self._success_rate = 1.0
            self._is_initializing = True

    def _fill_warm_pool(self):
        """Fill the warm pool with new IPs"""
        # A thread is dedicated to waiting on the warm pool to fill
        self._cluster.fill_warm_pool()
        self._warm_pool_triggered = True

    def _activate_warm_pool(self):
        """Activate the warm pool"""

        # While there are True values in the _thread_status dictionary
        while not all(not status for status in self._thread_status.values()):
            time.sleep(1)

        # Once all the threads are inactive, activate the warm pool
        with self._lock:
            self._cluster.activate_warm_pool()
            self._warm_pool_triggered = False
            self._success_rate = 1.0
            self._is_initializing = True

    def update(self, success: bool) -> None:
        """Update an IP with the result of a request."""
        with self._lock:
            thread_id = threading.get_ident()
            self._thread_status[thread_id] = False

            if success:
                self._is_initializing = False
                self._success_rate = min(self._success_rate + 0.1, 1.0)
            else:
                if not self._is_initializing:
                    self._success_rate = max(self._success_rate - 0.1, 0)

        # If the warm pool has not been triggered and the success rate is below
        # the warm threshold, fill the warm pool.
        # Force other threads to wait for the warm pool to be filled before
        # continuing.
        # ***Threads wait here for the warm pool to be filled***
        with self._warm_pool_condition:
            if (
                not self._warm_pool_triggered  # if the warm pool has not been triggered
                and self._success_rate < self._warm_threshold
            ):
                self._fill_warm_pool()

                # Tell all the threads that the warm pool has been filled
                self._warm_pool_condition.notify_all()

        # If the success rate is below the threshold, cycle the proxy servers.
        # ***Threads wait here for the reboot to complete***
        with self._reboot_condition:
            if self._success_rate < self._threshold:
                # If we don't have a warm pool, do a full reboot
                if not self._warm_pool_triggered:
                    self._reboot()

                # Otherwise, activate the warm pool
                else:
                    self._activate_warm_pool()
                # At this point, we should have an active proxy server cluster
                # Tell all threads waiting that the reboot has completed
                self._reboot_condition.notify_all()


class ThreadSafeCounter:
    """Thread-safe counter."""

    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()

    def increment(self):
        """Increment the counter safely."""
        with self._lock:
            self._count += 1

    @property
    def value(self):
        """Get the current count."""
        with self._lock:
            return self._count


class DataManager:
    """Manage the data structures."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

        # Load data from files
        self._locations = self._load_json(REMAINING_FILE)
        self._results = self._load_json(FINSIHED_FILE)
        self._failed = self._load_json(FAILED_FILE)
        _base_locations = self._load_json(BASE_FILE)
        self._TOTAL = len(_base_locations)  # pylint: disable=invalid-name

        self._url_retries = {}
        self._queue = queue.Queue()
        self._inital_processed = len(self._results) + len(self._failed)

        print(len(self._locations), len(self._results), len(self._failed), self._TOTAL)
        assert self._TOTAL == len(self._locations) + self._inital_processed

        for loc in self._locations:
            self._queue.put(loc)
        self._current = []

        self._start = time.perf_counter()

    def _load_json(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    @property
    def completion(self):
        """Completion Percentage"""
        with self._lock:
            processed = len(self._results) + len(self._failed) - self._inital_processed
            total = self._TOTAL - self._inital_processed
            return round((processed / total) * 100, 3)

    @property
    def total_completion(self):
        """Total Completion Percentage"""
        with self._lock:
            processed = len(self._results) + len(self._failed)
            return round((processed / self._TOTAL) * 100, 3)

    @property
    def next_business(self):
        """Next Location"""
        with self._lock:
            if not self._queue.empty():
                biz = self._queue.get()
                self._current.append(biz)
                return biz
            return None

    @property
    def complete(self):
        """Bool completion value."""
        with self._lock:
            return self._queue.empty()

    @property
    def elapsed(self) -> float:
        """The current elapsed time."""
        elapsed_time = time.perf_counter() - self._start
        minutes, seconds = divmod(elapsed_time, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    @property
    def status(self) -> str:
        """The status of the job"""
        return f"[{self.completion:.3f}% -- {self.elapsed} -- (Total: {self.total_completion:.3f}%)]"

    @property
    def counts(self) -> str:
        """The status of the job"""
        return f"Success: {len(self._results)} -- Failed: {len(self._failed)} -- Remaining: {len(self._locations)} || ({self._results + self._failed - self._inital_processed} / {self._TOTAL - self._inital_processed})"

    def success(self, data, ip) -> None:
        """Update with successful result."""
        with self._lock:
            self._results.append(data)
            # need to remove biz from current
            self._current = [biz for biz in self._current if biz["id"] != data["id"]]

        # Logging moved outside of the lock to avoid blocking
        print(
            f"{self.status} Successfully scraped description for {data['name']} with IP: {ip}"
        )

    def failed(self, data, ip, exception) -> None:
        """Update with failed result."""
        with self._lock:
            url = data["url"]
            self._url_retries[url] = self._url_retries.get(url, 0) + 1
            if self._url_retries[url] < 3:
                self._queue.put(data)
            else:
                self._failed.append(data)

            # need to remove biz from current
            self._current = [biz for biz in self._current if biz["id"] != data["id"]]

        # Logging moved outside of the lock
        print(
            f"{self.status} Failure scraping description for {data['name']} with IP: {ip} - {type(exception).__name__}"
        )

    def save_results(self):
        """Save results to a file."""
        with self._lock:
            queue_copy = list(self._queue.queue)
            locations = self._current + queue_copy
            self._dump_json(locations, REMAINING_FILE)
            self._dump_json(self._results, FINSIHED_FILE)
            self._dump_json(self._failed, FAILED_FILE)

    def _dump_json(self, data, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def log_status(self):
        """Log the current status."""
        print(f"{self.status} {self.counts}")


def scrape_locations(ip_manager, data_manager, counter):
    """Run the loop to scrape locations."""
    # Loop for the threads
    while True:
        ip = ip_manager.current
        biz = data_manager.next_business
        if not biz:
            break

        url = biz["url"]
        reviews, failed = scrape_business_reviews(url, format_proxy(ip))

        if failed:
            data_manager.failed(biz, ip, failed)
            ip_manager.update(False)

        else:
            biz["reviews"] = reviews
            data_manager.success(biz, ip)
            ip_manager.update(True)

        counter.increment()
        data_manager.save_results()

        if counter.value % 20 == 0:
            data_manager.log_status()


def scrape_locations_for_page_content(ip_manager, data_manager, counter):
    """Run the loop to scrape locations."""

    while True:
        ip = ip_manager.current
        biz = data_manager.next_business
        if not biz:
            break

        url = biz["url"]

        content, failed = scrape_business_page_content(url, format_proxy(ip))

        if failed:
            data_manager.failed(biz, ip, failed)
            ip_manager.update(False)

        else:
            biz["page_content"] = content
            data_manager.success(biz, ip)
            ip_manager.update(True)

        counter.increment()
        data_manager.save_results()

        if counter.value % 20 == 0:
            data_manager.log_status()


def main():
    """Main function"""

    locations = read_json()

    print(
        f"Srcaping Yelp Business Descriptions for {len(locations)} locations\n{'-'*80}"
    )
    NUM_WORKERS = 10
    IPS_PER_WORKER = 2

    # Read the JSON file containing the scraped data
    cluster = launch.ProxyCluster(num=NUM_WORKERS * IPS_PER_WORKER)

    data_manager = DataManager()
    ip_manager = IPManager(cluster)

    # Iterate until all the locations have been scraped
    counter = ThreadSafeCounter()

    try:
        with futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            print(f"Spinning up {NUM_WORKERS} worker threads.")

            try:
                _threads = {
                    executor.submit(
                        scrape_locations_for_page_content,
                        ip_manager,
                        data_manager,
                        counter,
                    )
                    for _ in range(5)
                }
                futures.wait(_threads)
            except KeyboardInterrupt:
                data_manager.save_results()
                os._exit(0)
            except launch.FailedToConnectToIP:
                print("Failed to connect to IP in cluster. Restarting script.")
                data_manager.save_results()
                main()

    except Exception as e:  # pylint: disable=W0718
        print(f"Error:\n{e}")

    if not data_manager.complete:
        data_manager.save_results()
        print("Restarting Script.")
        main()

    data_manager.save_results()
    launch.terminate_cluster()
    os._exit(0)


if __name__ == "__main__":
    # launch.terminate_cluster()
    main()
