# Computer Science Core: Operating Systems and Version Control

## Operating Systems: Process vs Thread
- Process: An executing program instance with its own isolated memory space, page tables, file descriptors, and Process Control Block (PCB).
- Thread: The smallest unit of execution inside a parent process. Threads share code, data, and heap memory but possess independent stacks, registers, and program counters.
- Comparison:
  - Context Switching: Processes require slower memory-space switching; threads switch CPU registers rapidly.
  - Communication: Processes communicate via Inter-Process Communication (IPC); threads communicate via shared process memory with synchronization locks.

## Memory Management and Virtual Memory
Virtual memory maps process logical addresses to physical RAM frames via the Memory Management Unit (MMU) and page tables.
- Paging: Divides physical memory into fixed-size frames and virtual address space into pages.
- Page Fault: Occurs when a requested page is not in physical RAM, requiring the OS to fetch the page from secondary disk storage.

## Git Version Control: Git Merge vs Git Rebase
- `git merge`: Combines divergent branches by creating a 3-way merge commit, preserving the exact branch history and chronological timeline.
- `git rebase`: Replays local commits sequentially onto the tip of the target branch, producing a linear, clean commit history.
- Best Practice: Rebase local feature branches before creating pull requests; never rebase shared/public main branches.
