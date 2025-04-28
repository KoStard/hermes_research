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

**Description:**
Create a concrete implementation of the `RemoteCopyInterface`. This implementation should handle copying multiple files specified in a source-to-target map to a remote server using a secure protocol like SCP or SFTP. It should leverage the `SSHConnectionInterface` for establishing the connection and potentially executing copy commands.

**Acceptance Criteria:**
*   A class implementing `RemoteCopyInterface` exists (e.g., `SCPRemoteCopy`).
*   The `remote_copy_files` method successfully copies files from local paths to specified remote paths.
*   The implementation handles potential errors during file transfer (e.g., connection issues, permission errors).
*   Directory creation on the remote host is handled if target paths don't exist.
*   Unit tests verify the copy functionality (potentially using mocking for SSH/SCP).

**Notes:**
Don't use paramiko, to use the ~/.ssh/config setup out of the box.

---

### Task: Define Strategy for Temporary Local Script

**ID:** TASK-003
**Status:** Open
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** Core Remote Execution Flow (Refinement)

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

**Description:**
Analyze the resources created during both local and remote execution flows (e.g., local research directory, remote *temporary* directory, remote *final* research directory structure potentially initiated by `mkdir`, local/remote tmux sessions, local temporary script file). Define and implement a robust error handling strategy that includes cleaning up these resources in case of failures at different stages (e.g., menu cancellation, SSH failure, copy failure, tmux failure). Pay special attention to cleaning up the remote temporary directory (`/tmp/hermes_research/{uuid}/`) upon successful start or failure during the remote setup process. Consider if maybe we can just leave the /tmp/ files, considering there might be some benefits to having these for reference/debugging.

**Acceptance Criteria:**
*   A clear strategy for error handling and resource cleanup is documented.
*   The `HermesResearchCLI.execute` method implements try/except/finally blocks or context managers to ensure cleanup.
*   Cleanup logic handles both successful completion and various failure scenarios.
*   The remote temporary directory is reliably removed after the remote command is successfully launched in tmux or if an error occurs during setup.
*   User feedback upon errors is clear and informative.

**Notes:**
Consider atomicity where possible. Remote cleanup commands will need to be sent via SSH. The cleanup of the remote temporary directory should ideally happen after the `tmux send-command` for the script execution is confirmed successful, or within error handling blocks.

---

### Task: Refine Remote Path Strategy

**ID:** TASK-005
**Status:** Open
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** Core Remote Execution Flow (Refinement)

**Description:**
Finalize and implement the strategy for determining paths for both local and remote execution. This includes:
1.  **Local:** The local research session path (e.g., `{local_research_dir}/{session_name}`).
2.  **Remote Final:** The *final* remote research directory path (used for `--deep-research`), derived from the configured `remote_research_path` and the `session_name` (e.g., `{remote_research_path}/{session_name}`).
3.  **Remote Temporary:** The *temporary* remote directory path for staging files and the script, generated uniquely for each run (e.g., `/tmp/hermes_research/{uuid}/`).
Ensure the `PathsManager` interface and implementation correctly support generating these paths and that the `HermesResearchCommandManager` uses the correct paths (`--deep-research` vs. file paths) depending on the execution context (local vs. remote).

**Acceptance Criteria:**
*   The local and remote path structures (final and temporary) are clearly defined and documented in `docs/cli_implementation_plan.md`.
*   `PathsManagerInterface` methods (`get_research_session_path`, `get_remote_files_folder`, `get_absolute_path`) are confirmed or updated to support these requirements.
*   `PathsManager` implementation correctly generates these paths, using POSIX conventions for remote paths. The temporary remote path is unique per invocation.
*   `HermesResearchCLI.execute` uses the `PathsManager` methods correctly for both local and remote scenarios.
*   `HermesResearchCommandManager.generate_command` correctly uses the final research path for `--deep-research` and the appropriate (local absolute or remote temporary) paths for `--textual_file` arguments based on the context.

**Notes:**
The existing `PathsManager` methods seem largely sufficient. This task focuses on ensuring they are correctly *applied* within the CLI and Command Manager logic for both local and remote flows as detailed in the implementation plan.

---

### Task: Implement SSHConnectionInterface

**ID:** TASK-006
**Status:** Open
**Priority:** High
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** TASK-001, TASK-002

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

---

### Task: Implement Core CLI Execution Logic

**ID:** TASK-007
**Status:** Open
**Priority:** High
**Assigned To:** Unassigned
**Depends On:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-006, TASK-008, TASK-009, TASK-010, TASK-011, TASK-012
**Blocks:** Application Entry Point

**Description:**
Implement the main orchestration logic within the `HermesResearchCLI.execute` method based on the steps outlined in `docs/cli_implementation_plan.md`. This involves coordinating the different manager components (Config, Menu, Paths, Command, Tmux, RemoteCopy, SSH) to handle both local and remote execution flows.

**Acceptance Criteria:**
*   `HermesResearchCLI.execute` correctly loads configuration using `ConfigManager`.
*   It uses `HermesResearchMenu` to gather user selections.
*   It correctly distinguishes between local and remote execution based on menu selection.
*   **Local Flow:**
    *   Gets local session path using `PathsManager`.
    *   Generates local command using `HermesResearchCommandManager`.
    *   Optionally saves the command script (TASK-012).
    *   Manages local tmux session creation and command sending using `TmuxManager` (including handling existing sessions via TASK-010).
*   **Remote Flow:**
    *   Retrieves remote server config and creates `SSHDestination`.
    *   Determines final remote research path and temporary remote path using `PathsManager`.
    *   Creates remote temporary directory using `SSHConnectionInterface`.
    *   Generates remote command using `HermesResearchCommandManager` (using correct remote paths).
    *   Creates temporary local script (TASK-003).
    *   Prepares file map for remote copy.
    *   Copies files and script to remote temp dir using `RemoteCopyInterface` (TASK-002).
    *   Configures `TmuxManager` for remote execution (TASK-001).
    *   Manages remote tmux session creation and command sending (including handling existing sessions via TASK-010).
    *   Cleans up local temporary script.
*   Error handling and resource cleanup are implemented (TASK-004).
*   User feedback is provided (TASK-011).

**Notes:**
This is the central task integrating most other components. Requires careful implementation following the plan.

---

### Task: Implement Dependency Injection Setup

**ID:** TASK-008
**Status:** Open
**Priority:** High
**Assigned To:** Unassigned
**Depends On:** All manager implementations (or their interfaces)
**Blocks:** TASK-007

**Description:**
Set up the dependency injection mechanism in the application's entry point (`src/hermes_research/main.py`). This involves instantiating the concrete implementations of all required manager interfaces (`PathsManager`, `ConfigManager`, `HermesResearchMenu`, `HermesResearchCommandManager`, `SubprocessSSHConnection`, `SCPRemoteCopy` (from TASK-002), `TmuxManager`) and injecting them into the `HermesResearchCLI` instance when it's created.

**Acceptance Criteria:**
*   `main.py` instantiates concrete implementations for all required interfaces.
*   These instances are passed to the `HermesResearchCLI` constructor.
*   The application runs without errors related to missing dependencies.

**Notes:**
Ensure that implementations requiring other managers (like `ConfigManager` needing `PathsManager`) are instantiated correctly.

---

### Task: Update CLI Argument Parsing

**ID:** TASK-009
**Status:** Open
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** TASK-007 (requires args)

**Description:**
Update the `HermesResearchCLI.define_cli` method to include the optional `-c` or `--command-args` argument for passing extra parameters directly to the underlying `hermes` command, as specified in `docs/cli_implementation_plan.md` and shown in `docs/use_case_remote.md`.

**Acceptance Criteria:**
*   `define_cli` includes an argument like `parser.add_argument("-c", "--command-args", ..., default="")`.
*   The parsed `args.command_args` value is correctly retrieved in `execute`.
*   The value is passed to `HermesResearchCommandManager.generate_command`.
*   The `hermes-research --help` output shows the new argument.

**Notes:**
Ensure the help text for the argument is clear.

---

### Task: Implement Tmux Session Name Handling

**ID:** TASK-010
**Status:** Open
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** TASK-001 (for remote)
**Blocks:** TASK-007 (uses this logic)

**Description:**
Implement the logic within `TmuxManager` (or potentially coordinated by `HermesResearchCLI`) to handle cases where a tmux session with the desired name already exists. This involves:
1.  Checking for existing sessions using `list_sessions()`.
2.  If a session exists, either:
    *   Implement `TmuxManager.determine_alternative_name` to suggest a new name (e.g., `session_name_1`).
    *   Prompt the user via `MenuManager` (or similar) to confirm overwriting (killing the old session) or entering a new name.

**Acceptance Criteria:**
*   When `create_session` is called (implicitly or explicitly) and the name exists, the user is prompted or an alternative name is generated.
*   The chosen name (original, new, or alternative) is used for subsequent `send_command` calls.
*   The logic works for both local and remote tmux sessions (leveraging TASK-001).
*   `TmuxManagerInterface` is updated if new methods like `determine_alternative_name` are added.

**Notes:**
Decide on the preferred strategy: automatic alternative name generation or user prompting. User prompting might be safer initially.

---

### Task: Implement User Feedback/Logging

**ID:** TASK-011
**Status:** Open
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** TASK-007 (integrates feedback)

**Description:**
Implement informative user feedback messages (using `print` or `logging.info`) within the `HermesResearchCLI.execute` method to guide the user through the process, matching the examples shown in `docs/use_case_local.md` and `docs/use_case_remote.md`. This includes messages for starting the session, copying files, creating tmux sessions, and providing instructions on how to attach. Also ensure debug logging (`logging.debug`) is used for more detailed internal steps.

**Acceptance Criteria:**
*   Key steps in both local and remote flows print informative messages to the console.
*   Messages closely match the format and content shown in the use case documents.
*   Error messages are clear and helpful.
*   Debug logging provides detailed information for troubleshooting.
*   Standard Python `logging` module is used.

**Notes:**
Ensure consistency in message formatting.

---

### Task: Implement Optional Local Command Saving

**ID:** TASK-012
**Status:** Open
**Priority:** Low
**Assigned To:** Unassigned
**Depends On:** TASK-007 (calls save)
**Blocks:** N/A

**Description:**
Implement the functionality to save the generated `hermes` command to a script file (e.g., `run_research.sh`) within the local research session directory when executing locally. This is mentioned as optional in `docs/cli_implementation_plan.md`. Use `HermesResearchCommandManager.save_command_in_file`.

**Acceptance Criteria:**
*   When running locally, a `run_research.sh` (or similar) file containing the exact command sent to tmux is saved in the session directory created by `PathsManager.get_research_session_path`.
*   The file saving happens before sending the command to tmux.
*   Directory creation for the session path is handled correctly (likely by `save_command_in_file` or ensured before calling it).

**Notes:**
This provides a record of the command run. Consider making this behavior configurable later if needed.

---

### Task: Create Project Plan

**ID:** TASK-013
**Status:** Done
**Priority:** High
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** N/A

**Description:**
Analyze the existing tasks (TASK-001 to TASK-012) and project documentation (`cli_implementation_plan.md`, use cases, philosophy) to create a comprehensive project plan. The plan should outline the sequence of task execution, identify dependencies, potential risks, open questions, and propose a high-level timeline or phasing.

**Acceptance Criteria:**
*   A new document `docs/tasks/TASK-013/project_plan.md` is created.
*   The plan includes sections for Charter/Scope, Risks, Dependencies/Sequence, Open Questions, and Timeline/Phasing.
*   The plan provides a logical order for tackling the existing implementation tasks.
*   Key risks and mitigation strategies are identified.
*   Open questions requiring clarification are listed.

**Notes:**
This task provides the strategic overview needed to execute the subsequent implementation tasks efficiently.
