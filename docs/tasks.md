# Hermes Research Tasks

## Task Template

```markdown
### Task - [STATUS]: [Short Title]

**ID:** TASK-XXX 
**Status:** Open | In Progress | Blocked | Done | Cancelled
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

**Test Requirements:**
- [ ] [Unit test for functionality 1]
- [ ] [Integration test for scenario 1]
- [ ] [Edge case test for situation 1]
- [ ] ...

**Notes:**
[Any additional notes, links, or considerations.]
```

---

## Pending Tasks

### Task - DONE: Implement Remote Tmux Functionality

**ID:** TASK-001
**Status:** Done
**Priority:** High
**Assigned To:** Completed
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

**Test Requirements:**
- [ ] Test `set_remote()` correctly configures TmuxManager for remote operations
- [ ] Test `list_sessions()` returns sessions from the remote host
- [ ] Test `create_session()` creates a tmux session remotely
- [ ] Test `send_command()` sends commands to the remote tmux session
- [ ] Test error handling for SSH connection failures
- [ ] Test error handling for tmux command failures on remote host
- [ ] Test with mock SSH connection to verify proper command formation

**Notes:**
The current `TmuxManager` implementation only handles local tmux. The interaction with `SSHConnectionInterface` needs careful design.

---

### Task - DONE: Implement RemoteCopyInterface

**ID:** TASK-002
**Status:** Done
**Priority:** High
**Assigned To:** AI Assistant
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

**Test Requirements:**
- [ ] Test `remote_copy_files()` successfully copies files to remote destination
- [ ] Test handling of non-existent target directories (auto-creation)
- [ ] Test error handling for connection failures
- [ ] Test error handling for permission issues
- [ ] Test error handling for invalid source paths
- [ ] Test with mock SSH connection to verify proper command formation
- [ ] Test handling of large files (performance test)
- [ ] Test handling of multiple files in a single operation

**Notes:**
Don't use paramiko, to use the ~/.ssh/config setup out of the box.

---

### Task - DONE: Define Strategy for Temporary Local Script

**ID:** TASK-003
**Status:** Done
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** Core Remote Execution Flow (Refinement)

**Description:**
For remote execution, a shell script containing the generated Hermes command is created locally before being copied to the remote server. We need to decide on the best approach for creating and managing this temporary local file. Options include using Python's `tempfile` module or creating it within a specific local temporary directory managed by the application.

**Acceptance Criteria:**
*   A decision is documented on where and how the temporary local script is created.
*   The temporary files are stored in /tmp for potential debugging/reference.
*   The implementation in `HermesResearchCLI.execute` reflects the chosen strategy.

**Test Requirements:**
- [ ] Test temporary file creation works as expected
- [ ] Test file content is correctly written
- [ ] Test handling of special characters in the command string

**Notes:**
Using Python's `tempfile` module with `tempfile.mkstemp()` to create files in /tmp with unique names. Files will be left in place for debugging purposes. Scripts will be executed using `. path/to/script.sh` to source them in the current shell environment without requiring executable permissions.

---

### Task - OPEN: Analyze and Implement Error Handling & Resource Cleanup

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

**Test Requirements:**
- [ ] Test cleanup after successful execution (both local and remote)
- [ ] Test cleanup after SSH connection failure
- [ ] Test cleanup after file copy failure
- [ ] Test cleanup after tmux command failure
- [ ] Test cleanup after user cancellation at different stages
- [ ] Test error message clarity and helpfulness
- [ ] Test proper handling of resource cleanup sequence
- [ ] Test cleanup with debug flag that preserves temporary files

**Notes:**
Consider atomicity where possible. Remote cleanup commands will need to be sent via SSH. The cleanup of the remote temporary directory should ideally happen after the `tmux send-command` for the script execution is confirmed successful, or within error handling blocks.

---

### Task - DONE: Refine Remote Path Strategy

**ID:** TASK-005
**Status:** Done
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

**Test Requirements:**
- [x] Test local research session path construction
- [x] Test remote final path construction with various session names
- [x] Test remote temporary path generation uniqueness
- [x] Test path construction with special characters in names
- [x] Test path normalization for different operating systems
- [x] Test command generation with correct paths for both contexts

**Notes:**
The existing `PathsManager` methods seem largely sufficient. This task focuses on ensuring they are correctly *applied* within the CLI and Command Manager logic for both local and remote flows as detailed in the implementation plan.

---

### Task - DONE: Implement SSHConnectionInterface

**ID:** TASK-006
**Status:** Done
**Priority:** High
**Assigned To:** Completed
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

**Test Requirements:**
- [x] Test successful command execution with mock subprocess
- [x] Test connection testing with various return scenarios
- [x] Test handling of timeout conditions
- [x] Test handling of authentication failures
- [x] Test handling of host key verification failures
- [x] Test with varied return codes and stderr messages
- [x] Test command execution with special characters
- [x] Test handling of large command output

**Notes:**
Consider edge cases like timeouts, host key checking, and different shell environments on the remote host. Using a library like Paramiko could be an alternative to `subprocess`.

---

### Task - DONE: Implement Temporary Command Script Creation

**ID:** TASK-014
**Status:** Done
**Priority:** High
**Assigned To:** Unassigned
**Depends On:** TASK-003
**Blocks:** Core Remote Execution Flow, Core Local Execution Flow

**Description:**
Implement the creation of a temporary script file containing the generated Hermes command in the /tmp directory for both local and remote execution flows. For local execution, this temporary script will be executed directly. For remote execution, it will be copied to the remote server before execution.

**Acceptance Criteria:**
*   `HermesResearchCommandManager` implements functionality to save the command to a temporary file in /tmp
*   Local execution flow uses this temporary script file by sourcing it with `. path/to/script.sh`
*   Remote execution flow uses this temporary script for copying to the remote server
*   Scripts are left in /tmp for potential debugging or reference

**Test Requirements:**
- [x] Test temporary script creation works as expected
- [x] Test script content is correctly written
- [x] Test script handles special characters in command
- [x] Test handling of failures during script creation

**Notes:**
This replaces the previous approach in TASK-012 which incorrectly saved the script to the research directory. The new approach uses a temporary file in /tmp that is appropriate for both local execution and remote copying. Scripts will be executed by sourcing them (`. path/to/script.sh`) rather than making them executable, to maintain the user's shell environment.

---

### Task - IN PROGRESS: Implement Core CLI Execution Logic

**ID:** TASK-007
**Status:** In Progress
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

**Test Requirements:**
- [x] Test configuration loading in CLI.execute()
- [ ] Test local flow execution end-to-end
- [ ] Test remote flow execution end-to-end
- [ ] Test correct branching between local and remote flows
- [ ] Test error handling in local flow
- [ ] Test error handling in remote flow
- [ ] Test session name handling and verification
- [ ] Test file mapping for remote copy
- [ ] Test command generation with correct paths
- [ ] Test remote temporary directory handling
- [ ] Test cleanup processes for both flows

**Notes:**
This is the central task integrating most other components. Requires careful implementation following the plan. Phase 1 (Local Flow) is complete. Phase 3 (Remote Flow Integration & Cleanup) is pending.

---

### Task - DONE: Implement Dependency Injection Setup

**ID:** TASK-008
**Status:** Done
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

**Test Requirements:**
- [x] Test main.py instantiates all required components
- [x] Test dependency order is correct (dependents after dependencies)
- [x] Test CLI construction with all dependencies injected
- [x] Test application startup with minimal configuration
- [x] Test error handling for missing/misconfigured dependencies

**Notes:**
Ensure that implementations requiring other managers (like `ConfigManager` needing `PathsManager`) are instantiated correctly.

---

### Task - DONE: Update CLI Argument Parsing

**ID:** TASK-009
**Status:** Done
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

**Test Requirements:**
- [x] Test CLI parser includes command-args option
- [x] Test help output shows the new argument with clear description
- [x] Test default value is set correctly
- [x] Test passing argument value works as expected
- [x] Test command-args is properly passed to generate_command

**Notes:**
Ensure the help text for the argument is clear.

---

### Task - DONE: Implement Tmux Session Name Handling

**ID:** TASK-010
**Status:** Done
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

**Test Requirements:**
- [x] Test detection of existing tmux sessions
- [x] Test user prompting for session management choices
- [x] Test handling when user chooses to overwrite existing session
- [x] Test handling when user chooses to use alternative name
- [ ] Test automatic alternative name generation logic
- [x] Test functionality works for remote tmux sessions
- [x] Test consistent session name is used for send_command after resolution

**Notes:**
Implemented user prompting strategy via HermesResearchCLI._handle_tmux_session_name() helper method. This approach keeps the session name handling logic in the CLI while allowing TmuxManager to focus on tmux operations. The automatic name generation approach was not implemented as the user prompting approach was deemed more user-friendly.

---

### Task - DONE: Implement User Feedback/Logging for Local Flow

**ID:** TASK-011
**Status:** Done
**Priority:** Medium
**Assigned To:** Unassigned
**Depends On:** N/A
**Blocks:** TASK-007 (integrates feedback)

**Description:**
Implement informative user feedback messages (using `print` or `logging.info`) within the `HermesResearchCLI.execute` method to guide the user through the process, matching the examples shown in `docs/use_case_local.md`. This includes messages for starting the session, creating tmux sessions, and providing instructions on how to attach. Also ensure debug logging (`logging.debug`) is used for more detailed internal steps.

**Acceptance Criteria:**
*   Key steps in local flow print informative messages to the console.
*   Messages closely match the format and content shown in the use case document.
*   Error messages are clear and helpful.
*   Debug logging provides detailed information for troubleshooting.
*   Standard Python `logging` module is used.

**Test Requirements:**
- [x] Test basic logging setup works correctly
- [x] Test local flow prints appropriate user messages
- [x] Test error messages are clear and helpful
- [x] Test debug logging captures detailed information
- [x] Test log messages match expected format from use case docs
- [x] Test consistent formatting across all message types

**Notes:**
Ensure consistency in message formatting without manual "INFO:" prefixes. The proper logging configuration handles formatting log messages.

---

### Task - DONE: Implement Remote Flow User Feedback/Logging

**ID:** TASK-015
**Status:** Done
**Priority:** Medium
**Assigned To:** Completed
**Depends On:** TASK-007
**Blocks:** N/A

**Description:**
Implement informative user feedback messages for the remote execution flow within the `HermesResearchCLI.execute` method, matching the examples shown in `docs/use_case_remote.md`. This includes messages for SSH connection testing, creating remote directories, copying files, managing remote tmux sessions, and providing instructions on how to attach.

**Acceptance Criteria:**
*   Key steps in the remote flow print informative messages to the console.
*   Messages closely match the format and content shown in the remote use case document.
*   Error messages for remote-specific failures are clear and helpful.
*   Debug logging provides detailed information for troubleshooting remote operations.
*   Standard Python `logging` module is used consistently with the local flow.

**Test Requirements:**
- [ ] Test remote flow prints appropriate user messages
- [ ] Test remote error messages are clear and helpful
- [ ] Test remote debug logging captures detailed information
- [ ] Test remote log messages match expected format from use case docs
- [ ] Test consistent formatting across all message types between local and remote flows

**Notes:**
This task should be implemented as part of the remote execution flow development. The feedback should follow the same format conventions as the local flow but include the additional SSH, file copying, and remote execution details.

---

### Task - CANCELLED: Implement Optional Local Command Saving

**ID:** TASK-012
**Status:** Cancelled
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

**Test Requirements:**
- [ ] Test command is correctly saved to file
- [ ] Test file is saved in the correct location
- [ ] Test directory is created if it doesn't exist
- [ ] Test file has correct permissions (executable)
- [ ] Test file content matches the command sent to tmux
- [ ] Test handling of special characters in commands

**Notes:**
This provides a record of the command run. Consider making this behavior configurable later if needed.

---

### Task - DONE: Create Project Plan

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

**Test Requirements:**
- [x] Verify project plan document exists in correct location
- [x] Verify all required sections are included
- [x] Verify dependencies match those in task definitions
- [x] Verify timeline is realistic based on task complexity
- [x] Verify risks have appropriate mitigation strategies
- [x] Verify plan follows project philosophy guidelines

**Notes:**
This task provides the strategic overview needed to execute the subsequent implementation tasks efficiently.
