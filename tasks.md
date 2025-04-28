# Hermes Research Tasks

## Task Template

```markdown
### Task: [Short Title]

**ID:** TASK-XXX 
**Status:** Open | In Progress | Blocked | Done
**Priority:** High | Medium | Low
**Assigned To:** Unassigned
**Depends On:** [List Task IDs or N/A]
**Blocks:** [List Task IDs or N/A]
**Date Created:** YYYY-MM-DD
**Date Updated:** YYYY-MM-DD

**Description:**
[Detailed description of the task, including goals and context.]

**Acceptance Criteria:**
*   [Criterion 1]
*   [Criterion 2]
*   ...

**Notes:**
[Any additional notes, links, or considerations.]
```

---

## Pending Tasks

### Task: Implement Remote Tmux Functionality

**ID:** TASK-001
**Status:** Open
**Priority:** High
**Assigned To:** Unassigned
**Depends On:** TASK-003 (SSH Interface assumed stable)
**Blocks:** Core Remote Execution Flow
**Date Created:** 2025-04-28
**Date Updated:** 2025-04-28

**Description:**
The `TmuxManager` needs to be extended or refactored to support executing tmux commands (list, create session, send command) on a remote server specified via `set_remote`. This will likely involve using the `SSHConnectionInterface` to run the necessary `tmux` commands on the remote host.

**Acceptance Criteria:**
*   `TmuxManager.set_remote(destination)` correctly configures the manager for remote operations.
*   `TmuxManager.list_sessions()` returns sessions from the specified remote host.
*   `TmuxManager.create_session(name)` creates a tmux session on the remote host.
*   `TmuxManager.send_command(session_name, command)` sends a command to the specified session on the remote host.
*   Appropriate error handling for SSH connection failures is implemented.
*   Unit tests verify remote functionality (potentially using mocking for SSH).

**Notes:**
The current `TmuxManager` implementation only handles local tmux. The interaction with `SSHConnectionInterface` needs careful design.

---

### Task: Implement RemoteCopyInterface

**ID:** TASK-002
**Status:** Open
**Priority:** High
**Assigned To:** Unassigned
**Depends On:** TASK-003 (SSH Interface assumed stable)
**Blocks:** Core Remote Execution Flow
**Date Created:** 2025-04-28
**Date Updated:** 2025-04-28

**Description:**
Create a concrete implementation of the `RemoteCopyInterface`. This implementation should handle copying multiple files specified in a source-to-target map to a remote server using a secure protocol like SCP or SFTP. It should leverage the `SSHConnectionInterface` for establishing the connection and potentially executing copy commands.

**Acceptance Criteria:**
*   A class implementing `RemoteCopyInterface` exists (e.g., `SCPRemoteCopy`).
*   The `remote_copy_files` method successfully copies files from local paths to specified remote paths.
*   The implementation handles potential errors during file transfer (e.g., connection issues, permission errors).
*   Directory creation on the remote host is handled if target paths don't exist.
*   Unit tests verify the copy functionality (potentially using mocking for SSH/SCP).

**Notes:**
Consider using libraries like `paramiko` or invoking `scp` via `subprocess` managed by `SSHConnectionInterface`. Ensure security best practices are followed.

---

### Task: Define Strategy for Temporary Local Script

**ID:** TASK-003
**Status:** Open
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** Core Remote Execution Flow (Refinement)
**Date Created:** 2025-04-28
**Date Updated:** 2025-04-28

**Description:**
For remote execution, a shell script containing the generated Hermes command is created locally before being copied to the remote server. We need to decide on the best approach for creating and managing this temporary local file. Options include using Python's `tempfile` module or creating it within a specific local temporary directory managed by the application.

**Acceptance Criteria:**
*   A decision is documented on where and how the temporary local script is created.
*   The chosen method ensures proper cleanup of the temporary file after it's copied or if an error occurs.
*   The implementation in `HermesResearchCLI.execute` reflects the chosen strategy.

**Notes:**
Using `tempfile.NamedTemporaryFile(delete=False)` and manually cleaning up might be a robust approach. Consider security implications of temporary file locations and permissions.

---

### Task: Analyze and Implement Error Handling & Resource Cleanup

**ID:** TASK-004
**Status:** Open
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** TASK-001, TASK-002, TASK-003
**Blocks:** N/A
**Date Created:** 2025-04-28
**Date Updated:** 2025-04-28

**Description:**
Analyze the resources created during both local and remote execution flows (e.g., local research directory, remote *temporary* directory, remote *final* research directory structure potentially initiated by `mkdir`, local/remote tmux sessions, local temporary script file). Define and implement a robust error handling strategy that includes cleaning up these resources in case of failures at different stages (e.g., menu cancellation, SSH failure, copy failure, tmux failure).

**Acceptance Criteria:**
*   A clear strategy for error handling and resource cleanup is documented.
*   The `HermesResearchCLI.execute` method implements try/except/finally blocks or context managers to ensure cleanup.
*   Cleanup logic handles both successful completion and various failure scenarios (including cleanup of the remote temporary directory).
*   User feedback upon errors is clear and informative.

**Notes:**
Consider atomicity where possible. For remote cleanup (especially the temporary directory), commands will need to be sent via SSH. Decide if cleanup should happen immediately after starting the tmux command or be left manual initially.

---

### Task: Refine Remote Path Strategy

**ID:** TASK-005
**Status:** Open
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** Core Remote Execution Flow (Refinement)
**Date Created:** 2025-04-28
**Date Updated:** 2025-04-28

**Description:**
Finalize the strategy for determining paths on the remote server. This includes:
1.  The *final* research directory path (used for `--deep-research`), derived from the configured `remote_research_path` and the `session_name`.
2.  The *temporary* directory path for staging files and the script, generated uniquely for each run.
Ensure the `PathsManager` interface and implementation correctly support generating these paths.

**Acceptance Criteria:**
*   The remote path structures (final and temporary) are clearly defined and documented.
*   `PathsManagerInterface` includes methods to generate the final remote research path (e.g., `get_research_session_path` adapted for remote base) and the temporary remote files folder (e.g., `get_remote_files_folder`).
*   `PathsManager` implementation correctly generates these paths, using POSIX path conventions for remote paths. The temporary path should be unique per invocation.
*   `HermesResearchCLI.execute` uses the defined `PathsManager` methods appropriately.

**Notes:**
The existing `get_research_session_path` can likely be reused if the base path is passed correctly. The existing `get_remote_files_folder` seems suitable for the temporary path. This task confirms these methods meet the requirements for the remote flow.

---

### Task: Implement SSHConnectionInterface

**ID:** TASK-006
**Status:** Open
**Priority:** High
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** TASK-001, TASK-002
**Date Created:** 2025-04-28
**Date Updated:** 2025-04-28

**Description:**
Ensure a robust implementation of `SSHConnectionInterface` exists. The current `SubprocessSSHConnection` is a good start, but needs thorough testing and potentially refinement for handling various SSH configurations, authentication methods (keys, passwords - though keys are preferred), and edge cases.

**Acceptance Criteria:**
*   `SubprocessSSHConnection` (or alternative implementation) reliably executes commands remotely.
*   `test_connection` accurately reflects connectivity.
*   Handles different SSH return codes and stderr messages appropriately.
*   Authentication methods are considered (initially focusing on key-based auth assumed configured system-wide).
*   Comprehensive unit tests cover various scenarios.

**Notes:**
Consider edge cases like timeouts, host key checking, and different shell environments on the remote host. Using a library like Paramiko could be an alternative to `subprocess`.
