import uuid

from mcp_server import (
    enqueue,
    orchestrate,
    MCPTask,
    CONFLUENCE_INTELLIGENT_ANALYZE,
    set_progress_callback,
)


def main() -> None:
    set_progress_callback(
        lambda task_id, status, value: print(f"[{task_id}] {status} {value}")
    )
    enqueue(
        MCPTask(
            task_id=str(uuid.uuid4()),
            task_type=CONFLUENCE_INTELLIGENT_ANALYZE,
            params={"demo": True},
        )
    )
    orchestrate()
    print("Edge agent: MCP run complete")


if __name__ == "__main__":
    main()
