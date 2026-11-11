import copy

class MemoryBlock:
    def __init__(self, size, is_hole=True, process_id=None):
        self.size = size
        self.is_hole = is_hole
        self.process_id = process_id

    def __repr__(self):
        if self.is_hole:
            return f"[Hole: {self.size} KB]"
        else:
            return f"[{self.process_id}: {self.size} KB]"


class MemoryManager:
    def __init__(self, initial_holes):
        # Initialize memory with a list of holes
        self.memory = [MemoryBlock(size=h) for h in initial_holes]
        self.allocated_processes = {}  # pid -> (block_index, size)

    def allocate_first_fit(self, pid, size):
        for idx, block in enumerate(self.memory):
            if block.is_hole and block.size >= size:
                self._place_process(idx, pid, size)
                return True
        return False

    def allocate_best_fit(self, pid, size):
        best_idx = -1
        best_size = float('inf')
        
        for idx, block in enumerate(self.memory):
            if block.is_hole and block.size >= size:
                if block.size < best_size:
                    best_size = block.size
                    best_idx = idx
                    
        if best_idx != -1:
            self._place_process(best_idx, pid, size)
            return True
        return False

    def allocate_worst_fit(self, pid, size):
        worst_idx = -1
        worst_size = -1
        
        for idx, block in enumerate(self.memory):
            if block.is_hole and block.size >= size:
                if block.size > worst_size:
                    worst_size = block.size
                    worst_idx = idx
                    
        if worst_idx != -1:
            self._place_process(worst_idx, pid, size)
            return True
        return False

    def _place_process(self, idx, pid, size):
        hole = self.memory[idx]
        remaining = hole.size - size
        
        # Replace original hole with allocated process block
        self.memory[idx] = MemoryBlock(size=size, is_hole=False, process_id=pid)
        self.allocated_processes[pid] = size
        
        # Insert remaining space as a new smaller hole right after
        if remaining > 0:
            self.memory.insert(idx + 1, MemoryBlock(size=remaining, is_hole=True))

    def deallocate(self, pid):
        found = False
        for idx, block in enumerate(self.memory):
            if not block.is_hole and block.process_id == pid:
                block.is_hole = True
                block.process_id = None
                found = True
                break
        
        if found:
            self._coalesce_adjacent_holes()
            if pid in self.allocated_processes:
                del self.allocated_processes[pid]
        return found

    def _coalesce_adjacent_holes(self):
        """Merges contiguous free blocks into a single larger hole."""
        i = 0
        while i < len(self.memory) - 1:
            if self.memory[i].is_hole and self.memory[i+1].is_hole:
                self.memory[i].size += self.memory[i+1].size
                self.memory.pop(i + 1)
            else:
                i += 1

    def get_fragmentation_metrics(self):
        total_free = sum(b.size for b in self.memory if b.is_hole)
        holes = [b.size for b in self.memory if b.is_hole]
        largest_hole = max(holes) if holes else 0
        
        # External fragmentation: total free memory available that cannot be used 
        # as a single block (or total free memory minus largest contiguous hole)
        external_frag = total_free - largest_hole
        
        return {
            "total_free_memory": total_free,
            "largest_usable_hole": largest_hole,
            "external_fragmentation": external_frag,
            "internal_fragmentation": 0  # Dynamic partitioning yields 0 internal frag
        }

    def print_state(self):
        map_str = " -> ".join([str(b) for b in self.memory])
        print(f"  Memory Map: {map_str}")


def run_simulation(strategy_name, initial_holes, workload):
    print("=" * 70)
    print(f" STRATEGY: {strategy_name.upper()}")
    print("=" * 70)
    
    sim = MemoryManager(initial_holes)
    print("Initial State:")
    sim.print_state()
    print("-" * 70)

    for step in workload:
        action = step["action"]
        pid = step["pid"]
        
        if action == "allocate":
            size = step["size"]
            if strategy_name == "First-Fit":
                success = sim.allocate_first_fit(pid, size)
            elif strategy_name == "Best-Fit":
                success = sim.allocate_best_fit(pid, size)
            elif strategy_name == "Worst-Fit":
                success = sim.allocate_worst_fit(pid, size)
                
            status = "ALLOCATED" if success else "REJECTED (Insufficient contiguous space)"
            print(f"Action: Allocate {pid} ({size} KB) ---> {status}")
            
        elif action == "deallocate":
            success = sim.deallocate(pid)
            status = "FREED & COALESCED" if success else "NOT FOUND"
            print(f"Action: Deallocate {pid} ---> {status}")
            
        sim.print_state()
        print()

    # Final summary reports
    metrics = sim.get_fragmentation_metrics()
    print("-" * 70)
    print("FINAL SUMMARY & FRAGMENTATION METRICS:")
    print(f"  Successfully Allocated Processes : {list(sim.allocated_processes.keys())}")
    print(f"  Total Free Memory                : {metrics['total_free_memory']} KB")
    print(f"  Largest Usable Contiguous Hole   : {metrics['largest_usable_hole']} KB")
    print(f"  Internal Fragmentation           : {metrics['internal_fragmentation']} KB")
    print(f"  External Fragmentation           : {metrics['external_fragmentation']} KB")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Test Data from Assignment Specifications
    INITIAL_HOLES = [100, 500, 200, 300, 600]
    
    WORKLOAD = [
        {"action": "allocate", "pid": "P1", "size": 212},
        {"action": "allocate", "pid": "P2", "size": 417},
        {"action": "allocate", "pid": "P3", "size": 112},
        {"action": "allocate", "pid": "P4", "size": 426},
        {"action": "deallocate", "pid": "P2"},
        {"action": "allocate", "pid": "P5", "size": 200},
    ]

    # Run simulation on all 3 strategies independently
    for strategy in ["First-Fit", "Best-Fit", "Worst-Fit"]:
        run_simulation(strategy, INITIAL_HOLES, WORKLOAD)