# Use Case: Local Execution

This document illustrates the user experience when running `hermes-research` and choosing to execute the research task locally.

## Scenario

A user wants to start a new research session named "local_llm_test" using the "llama3-local" model with a budget of 50. They have two files, `report.pdf` and `data.csv`, they want to include. They will run the command directly on their machine.

## User Interaction Flow

1.  **User invokes the command:**

    ```bash
    hermes-research report.pdf data.csv
    ```

2.  **Application prompts for session name:**

    ```text
    Enter a name for this research session: local_llm_test
    ```

3.  **Application prompts for model selection:** (Assuming "llama3-local" and "gpt-4-remote" are configured)

    ```text

    --- Select Model ---
    1: llama3-local
    2: gpt-4-remote
    Enter 'q' to cancel
    Choice: 1
    ```

4.  **Application prompts for budget:** (Assuming default is 30)

    ```text
    Enter budget (default: 30): 50
    ```

5.  **Application prompts for the research query:**

    ```text
    Enter the research prompt (press Meta+Enter or Esc+Enter to finish):
    > Analyze the key findings in the attached report, correlating them
    > with the trends observed in the data.csv file.
    > Summarize the main conclusions.
    > [Meta+Enter or Esc+Enter is pressed]
    ```

6.  **Application prompts for execution target:** (Assuming no remote servers are configured or user chooses local)

    ```text

    --- Select Execution Target ---
    1: Local Execution
    Enter 'q' to cancel
    Choice: 1
    ```
    *(Alternatively, if remote servers exist)*
    ```text

    --- Select Execution Target ---
    1: Local Execution
    2: server-alpha
    3: server-beta
    Enter 'q' to cancel
    Choice: 1
    ```

7.  **Application confirms local execution and starts tmux:**

    ```text
    Starting local research session 'local_llm_test'...
    Creating tmux session 'local_llm_test'...
    Sending command to tmux session...
    Local research session 'local_llm_test' started in tmux.
    You can attach to it using: tmux attach -t local_llm_test
    ```

## Result

*   A new tmux session named `local_llm_test` is created on the user's local machine.
*   The `hermes` command, configured with the selected model, budget, prompt, and absolute paths to `report.pdf` and `data.csv`, is executed within that tmux session.
*   The research directory (e.g., `~/hermes_research_data/local_llm_test/`) is created locally.
*   A command script might optionally be saved within the research directory.
