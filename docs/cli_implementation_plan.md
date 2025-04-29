# HermesResearchCLI Implementation Plan

This document outlines the implementation strategy for the `HermesResearchCLI.execute` method, which orchestrates the process of preparing and launching a Hermes research task either locally or on a remote server via tmux.

## Core Logic Flow

The `execute` method acts as the central coordinator, leveraging various manager components provided via dependency injection.

```mermaid
graph TD
    A[Start execute args ] --> B{Load Config};
    B --> C{Display Menu & Get Selection};
    C --> D{Local or Remote?};
    D -- Local --> E[Local Execution Flow];
    D -- Remote --> F[Remote Execution Flow];
    E --> G[End];
    F --> G;

    subgraph Dependencies
        dep1[ConfigManager]
        dep2[HermesResearchMenu]
        dep3[PathsManager]
        dep4[HermesResearchCommandManager]
        dep5[TmuxManager]
        dep6[RemoteCopyInterface]
        dep7[SSHConnectionInterface]
    end

    B --> dep1;
    C --> dep2;
    E --> dep3;
    E --> dep4;
    E --> dep5;
    F --> dep1;
    F --> dep3;
    F --> dep4;
    F --> dep5;
    F --> dep6;
    F --> dep7;

```

**Steps:**

1.  **Receive Arguments (`args`):** Get parsed command-line arguments, including file paths and any extra Hermes arguments (`-c`).
2.  **Load Configuration:** Use `ConfigManager` to load `HermesConfig`.
3.  **Get User Selection:**
    *   Instantiate `HermesResearchMenu`.
    *   Set the loaded `config` on the menu instance.
    *   Call `menu.get_selection()` to interactively gather `session_name`, `model`, `budget`, `prompt`, and `selected_server_name`.
4.  **Determine Execution Target:** Check if `MenuSelection.selected_server_name` is `None`.
    *   If `None`, proceed to **Local Execution Flow**.
    *   If a server name is present, proceed to **Remote Execution Flow**.

## Local Execution Flow

This path executes the Hermes command directly on the local machine within a tmux session.

```mermaid
graph TD
    subgraph Local Execution
        LE1[Get Local Session Path] --> LE2[Generate Local Command];
        LE2 --> LE3[Save Command Script Optional];
        LE3 --> LE4{Tmux Session Exists?};
        LE4 -- No --> LE5[Create Local Tmux Session];
        LE4 -- Yes --> LE6[Get Alternative Name / Confirm Overwrite];
        LE6 --> LE5;
        LE5 --> LE7[Send Command to Tmux];
        LE7 --> LE_End[Execution Started];
    end

    LE1 -- Uses --> dep3[PathsManager];
    LE2 -- Uses --> dep4[HermesResearchCommandManager];
    LE4 -- Uses --> dep5[TmuxManager];
    LE5 -- Uses --> dep5;
    LE7 -- Uses --> dep5;
```

**Steps:**

1.  **Get Session Path:** Use `PathsManager.get_research_session_path` with the `research_directory` from config and the selected `session_name`.
2.  **Generate Command:** Use `HermesResearchCommandManager.generate_command`, providing:
    *   The local session path.
    *   Selected `model`, `budget`, `prompt`.
    *   Absolute paths of input files (`args.files`), resolved using `PathsManager.get_absolute_path`.
    *   Extra arguments (`args.extra_args`).
3.  **Save Command (Optional):** Use `HermesResearchCommandManager.save_command_in_file` to save the generated command to a script file within the session path for reference or debugging.
4.  **Manage Tmux Session:**
    *   Use `TmuxManager.list_sessions()` to check if a session with `session_name` already exists.
    *   If it exists, use `TmuxManager.determine_alternative_name` or prompt the user to confirm overwriting or choose a new name. Update `session_name` if necessary.
    *   Use `TmuxManager.create_session(session_name)`.
    *   Use `TmuxManager.send_command(session_name, generated_command)`.

## Remote Execution Flow

This path sets up the research on a configured remote server, copies necessary files, and starts the command in a remote tmux session.

```mermaid
graph TD
    subgraph Remote Execution
        RE1[Get Remote Server Config] --> RE1a[Define Final Remote Research Path];
        RE1a --> RE1b[Define Remote Temp Path];
        RE1b --> RE1c[Create Remote Temp Dir];
        RE1c --> RE3[Generate Remote Command];
        RE3 --> RE4[Create Local Temp Script];
        RE4 --> RE5[Prepare File Map to Temp Dir];
        RE5 --> RE6[Copy Files & Script to Remote Temp Dir];
        RE6 --> RE7[Configure Tmux for Remote];
        RE7 --> RE8{Remote Tmux Session Exists?};
        RE8 -- No --> RE9[Create Remote Tmux Session];
        RE8 -- Yes --> RE10[Get Alternative Name / Confirm Overwrite];
        RE10 --> RE9;
        RE9 --> RE11[Send Script Execution Command to Remote Tmux];
        RE11 --> RE12[Cleanup Local Temp Script];
        RE12 --> RE_End[Remote Execution Started];
    end

    RE1 -- Uses --> dep1[ConfigManager];
    RE2 -- Uses --> dep3[PathsManager];
    RE3 -- Uses --> dep4[HermesResearchCommandManager];
    RE5 -- Uses --> dep3;
    RE6 -- Uses --> dep6[RemoteCopyInterface];
    RE6 -- Needs --> dep7[SSHConnectionInterface];
    RE7 -- Uses --> dep5[TmuxManager];
    RE8 -- Uses --> dep5;
    RE9 -- Uses --> dep5;
    RE11 -- Uses --> dep5;

```

**Steps:**

1.  **Get Remote Config:** Retrieve the `HermesConfigRemoteServer` details (hostname, username, `remote_research_path`) from the loaded `config` using `MenuSelection.selected_server_name`. Create an `SSHDestination` object.
2.  **Define Final Remote Research Path:** Determine the final path where Hermes will store its results on the remote server (e.g., `{remote_research_path}/{session_name}`). This path is used for the `--deep-research` argument.
3.  **Define Remote Temp Path:** Use `PathsManager.get_remote_files_folder()` to generate a unique temporary directory path on the remote server (e.g., `/tmp/hermes_research/{uuid}/`). This path will be used for staging files.
4.  **Create Remote Temp Dir:** Use `SSHConnectionInterface.execute_command_on_remote` to execute `mkdir -p {remote_temp_path}` on the remote server. Check for success.
5.  **Generate Remote Command:** Use `HermesResearchCommandManager.generate_command`, providing:
    *   The *final remote research path* (from step 2) for the `--deep-research` argument.
    *   Selected `model`, `budget`, `prompt`.
    *   *Remote temporary paths* for the input files (using the base names of `args.files` appended to the remote temporary path from step 3).
    *   Extra arguments (`args.extra_args`).
6.  **Create Local Temp Script:** Create a temporary script file locally containing the generated command (from step 5).
7.  **Prepare File Map to Temp Dir:** Create a dictionary mapping local source paths to remote *temporary* target paths:
    *   Map each absolute local input file path (`PathsManager.get_absolute_path(f)`) to its corresponding path within the remote temporary directory (e.g., `{remote_temp_path}/{basename(f)}`).
    *   Map the local temporary script path (from step 6) to a path within the remote temporary directory (e.g., `{remote_temp_path}/run_research.sh`). Let's call this the `remote_script_temp_path`.
8.  **Copy Files to Remote Temp Dir:** Use `RemoteCopyInterface.remote_copy_files` with the file map (from step 7) and the `SSHDestination`.
9.  **Configure Tmux for Remote:** Use `TmuxManager.set_remote(selected_server_name)`.
10. **Manage Remote Tmux Session:**
    *   Use `TmuxManager.list_sessions()` (which now operates remotely) to check for existing sessions with the target `session_name`.
    *   Handle existing sessions as in the local flow (alternative name/overwrite confirmation). Update `session_name` if needed.
    *   Use `TmuxManager.create_session(session_name)`.
    *   Generate the command to execute the script *from its temporary location* on the remote machine (e.g., `. {remote_script_temp_path}`).
    *   Use `TmuxManager.send_command(session_name, script_execution_command)`.
11. **Cleanup:**
    *   Delete the local temporary script file (from step 6).
    *   *(Optional/Future Task)* Consider adding logic to clean up the remote temporary directory (`{remote_temp_path}`) after the script starts successfully, or leave it for debugging. See TASK-004.

## Dependency Injection

The `HermesResearchCLI` class will receive instances of all required manager interfaces (`ConfigManagerInterface`, `HermesResearchMenuInterface`, `PathsManagerInterface`, `HermesResearchCommandManagerInterface`, `TmuxManagerInterface`, `RemoteCopyInterface`, `SSHConnectionInterface`) through its constructor. The `main` function or application entry point will be responsible for instantiating the concrete implementations and injecting them.

## CLI Argument Parsing (`define_cli`)

The `define_cli` method needs to be updated:

1.  Keep the `files` positional argument (`nargs="*"`).
2.  Add an optional argument for extra parameters, e.g., `-c` or `--command-args`:
    ```python
    parser.add_argument(
        "-c", "--command-args",
        help="Additional arguments to pass directly to the hermes command, enclosed in quotes.",
        type=str,
        default=""
    )
    ```
The `args.command_args` value will then be passed to `HermesResearchCommandManager.generate_command`.
