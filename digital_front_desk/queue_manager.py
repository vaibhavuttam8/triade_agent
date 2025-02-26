from .models import QueueItem, UrgencyLevel
from .telemetry import telemetry
from typing import Optional, List
import heapq
import time
from datetime import datetime, timedelta

class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._entry_count = 0
        self._removed_entries = set()

    def add(self, item: QueueItem):
        # Priority is negative urgency level (so higher urgency = lower number = higher priority)
        # Secondary sort by timestamp
        priority = (-item.urgency_level.value, item.timestamp.timestamp())
        entry = [priority, self._entry_count, item]
        self._entry_count += 1
        heapq.heappush(self._queue, entry)

    def remove(self, user_id: str):
        self._removed_entries.add(user_id)

    def pop(self) -> Optional[QueueItem]:
        while self._queue:
            priority, count, item = heapq.heappop(self._queue)
            if item.user_id not in self._removed_entries:
                return item
        return None

    def peek(self) -> Optional[QueueItem]:
        while self._queue:
            priority, count, item = self._queue[0]
            if item.user_id not in self._removed_entries:
                return item
            heapq.heappop(self._queue)
        return None

class QueueManager:
    def __init__(self):
        self.queues = {
            UrgencyLevel.CRITICAL: PriorityQueue(),
            UrgencyLevel.HIGH: PriorityQueue(),
            UrgencyLevel.MEDIUM: PriorityQueue(),
            UrgencyLevel.LOW: PriorityQueue()
        }
        
        # Metrics
        self.queue_sizes = {level: 0 for level in UrgencyLevel}
        self.wait_times = []

    def add_to_queue(self, item: QueueItem):
        with telemetry.tracer.start_as_current_span("queue_add_item") as span:
            span.set_attributes({
                "queue.urgency_level": item.urgency_level.value,
                "queue.user_id": item.user_id
            })
            
            self.queues[item.urgency_level].add(item)
            self.queue_sizes[item.urgency_level] += 1
            
            # Record metrics
            self._record_queue_metrics()

    def get_next_item(self) -> Optional[QueueItem]:
        with telemetry.tracer.start_as_current_span("queue_get_next") as span:
            # Try to get items in order of urgency
            for level in UrgencyLevel:
                item = self.queues[level].pop()
                if item:
                    self.queue_sizes[level] -= 1
                    
                    # Calculate and record wait time
                    wait_time = (datetime.now() - item.timestamp).total_seconds()
                    self.wait_times.append(wait_time)
                    
                    span.set_attributes({
                        "queue.item_found": True,
                        "queue.urgency_level": level.value,
                        "queue.wait_time": wait_time
                    })
                    
                    # Record metrics
                    self._record_queue_metrics()
                    return item
            
            span.set_attributes({"queue.item_found": False})
            return None

    def remove_from_queue(self, user_id: str):
        with telemetry.tracer.start_as_current_span("queue_remove_item") as span:
            span.set_attributes({"queue.user_id": user_id})
            
            # Remove from all queues (user should only be in one, but being thorough)
            for queue in self.queues.values():
                queue.remove(user_id)
            
            # Record metrics
            self._record_queue_metrics()

    def get_queue_status(self) -> dict:
        return {
            "queue_sizes": self.queue_sizes,
            "average_wait_time": sum(self.wait_times) / len(self.wait_times) if self.wait_times else 0,
            "total_items": sum(self.queue_sizes.values())
        }

    def _record_queue_metrics(self):
        # Record queue sizes
        for level, size in self.queue_sizes.items():
            telemetry.meter.create_counter(
                name=f"queue.size.{level.name.lower()}",
                description=f"Number of items in {level.name} queue",
                unit="1"
            ).add(size)
        
        # Record average wait time
        if self.wait_times:
            telemetry.meter.create_histogram(
                name="queue.wait_time",
                description="Wait time for items in queue",
                unit="s"
            ).record(sum(self.wait_times) / len(self.wait_times))

# Global instance
queue_manager = QueueManager() 