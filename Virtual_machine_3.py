import threading
import time
import random
from dataclasses import dataclass, field
from typing import List


@dataclass
class Host:
    id: int
    cpu_capacity: int
    mem_capacity: int
    cpu_used: int = 0
    mem_used: int = 0

    def can_place(self, vm) -> bool:
        return (self.cpu_used + vm.cpu <= self.cpu_capacity) and (self.mem_used + vm.mem <= self.mem_capacity)

    def place(self, vm) -> None:
        self.cpu_used += vm.cpu
        self.mem_used += vm.mem

    def remove(self, vm) -> None:
        # subtract resources when VM finishes; guard against negative values
        self.cpu_used = max(0, self.cpu_used - vm.cpu)
        self.mem_used = max(0, self.mem_used - vm.mem)


@dataclass
class VMRequest:
    id: int
    cpu: int
    mem: int
    duration: float  # seconds


@dataclass
class Scheduler:
    hosts: List[Host] = field(default_factory=list)
    placed: dict = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def schedule_vm(self, vm: VMRequest) -> bool:
        # First-fit placement
        for h in self.hosts:
            with self.lock:
                if h.can_place(vm):
                    h.place(vm)
                    self.placed[vm.id] = (vm, h)
                    print(f"Placed VM{vm.id} on Host{h.id} (cpu {h.cpu_used}/{h.cpu_capacity})")
                    threading.Thread(target=self._run_vm, args=(vm, h), daemon=True).start()
                    return True
        print(f"Failed to place VM{vm.id} (no capacity)")
        return False

    def _run_vm(self, vm: VMRequest, host: Host) -> None:
        time.sleep(vm.duration)  # simulate runtime
        # VM finishes
        with self.lock:
            host.remove(vm)
            # remove placement entry if still present
            if vm.id in self.placed:
                del self.placed[vm.id]
            print(f"VM{vm.id} finished on Host{host.id} (cpu {host.cpu_used}/{host.cpu_capacity})")


# demo
hosts = [Host(i, cpu_capacity=8, mem_capacity=32) for i in range(3)]


def demo():
    sched = Scheduler(hosts=hosts)
    # create random VM requests
    for i in range(10):
        vm = VMRequest(
            id=i,
            cpu=random.choice([1, 2, 4]),
            mem=random.choice([1, 2, 4, 8]),
            duration=random.uniform(2, 6)
        )
        sched.schedule_vm(vm)
        time.sleep(random.uniform(0.2, 1.0))

    # wait for all to finish
    while sched.placed:
        time.sleep(0.5)


if __name__ == "__main__":
    demo()
