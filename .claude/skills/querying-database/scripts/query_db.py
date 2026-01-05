#!/usr/bin/env python3
"""
Query the automations database via API or direct Supabase connection.

Usage:
    python3 query_db.py logs [--limit N] [--status STATUS] [--automation SLUG] [--tag TAG]
    python3 query_db.py log-detail LOG_ID
    python3 query_db.py automations [--type TYPE] [--status STATUS] [--category CAT]
    python3 query_db.py automation-detail SLUG
    python3 query_db.py stats
    python3 query_db.py failed [--limit N]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

# Try API first, fall back to direct Supabase if available
API_URL = os.getenv("API_URL", "https://api.columnline.dev")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from supabase import create_client
    HAS_SUPABASE = (
        os.getenv("SUPABASE_URL") and
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
except ImportError:
    HAS_SUPABASE = False


def get_supabase():
    """Get Supabase client if available."""
    if not HAS_SUPABASE:
        return None
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )


def api_get(endpoint: str, params: dict = None) -> dict:
    """Make GET request to API."""
    if not HAS_REQUESTS:
        print("Error: requests library not installed. Run: pip install requests")
        sys.exit(1)

    url = f"{API_URL}{endpoint}"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def format_timestamp(ts: str) -> str:
    """Format ISO timestamp to readable format."""
    if not ts:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts[:19] if len(ts) > 19 else ts


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds is None:
        return "N/A"
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        return f"{seconds/60:.1f}m"


def print_table(rows: list, headers: list):
    """Print formatted table."""
    if not rows:
        print("No results found.")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Print header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))

    # Print rows
    for row in rows:
        print(" | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def cmd_logs(args):
    """List execution logs."""
    params = {"limit": args.limit}
    if args.status:
        params["status"] = args.status
    if args.automation:
        params["automation_slug"] = args.automation
    if args.tag:
        params["tag"] = args.tag

    try:
        data = api_get("/logs", params)
        logs = data if isinstance(data, list) else data.get("logs", [])
    except Exception as e:
        # Fall back to Supabase
        sb = get_supabase()
        if not sb:
            print(f"API error: {e}")
            print("Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
            sys.exit(1)

        query = sb.table("execution_logs").select("*").order("started_at", desc=True).limit(args.limit)
        if args.status:
            query = query.eq("status", args.status)
        if args.automation:
            query = query.eq("automation_slug", args.automation)
        logs = query.execute().data

    rows = []
    for log in logs:
        rows.append([
            log.get("id", "")[:8],
            log.get("automation_slug") or log.get("worker_name", "")[:30],
            log.get("status", ""),
            format_duration(log.get("runtime_seconds")),
            format_timestamp(log.get("started_at")),
        ])

    print_table(rows, ["ID", "Automation/Worker", "Status", "Duration", "Started"])


def cmd_log_detail(args):
    """Get full log details."""
    try:
        log = api_get(f"/logs/{args.log_id}")
    except Exception as e:
        sb = get_supabase()
        if not sb:
            print(f"API error: {e}")
            sys.exit(1)

        result = sb.table("execution_logs").select("*").eq("id", args.log_id).single().execute()
        log = result.data

    if not log:
        print(f"Log {args.log_id} not found.")
        return

    print(f"\n{'='*60}")
    print(f"LOG: {log.get('id')}")
    print(f"{'='*60}")
    print(f"Automation: {log.get('automation_slug') or 'N/A'}")
    print(f"Worker:     {log.get('worker_name') or 'N/A'}")
    print(f"Status:     {log.get('status')}")
    print(f"Started:    {format_timestamp(log.get('started_at'))}")
    print(f"Completed:  {format_timestamp(log.get('completed_at'))}")
    print(f"Duration:   {format_duration(log.get('runtime_seconds'))}")
    print(f"Tags:       {', '.join(log.get('tags') or [])}")

    if log.get("input"):
        print(f"\n{'─'*40}")
        print("INPUT:")
        print(json.dumps(log["input"], indent=2, default=str)[:2000])

    if log.get("output"):
        print(f"\n{'─'*40}")
        print("OUTPUT:")
        output_str = json.dumps(log["output"], indent=2, default=str)
        print(output_str[:3000])
        if len(output_str) > 3000:
            print(f"... (truncated, full output is {len(output_str)} chars)")

    if log.get("error"):
        print(f"\n{'─'*40}")
        print("ERROR:")
        print(json.dumps(log["error"], indent=2, default=str))


def cmd_automations(args):
    """List automations."""
    params = {}
    if args.type:
        params["type"] = args.type
    if args.status:
        params["status"] = args.status
    if args.category:
        params["category"] = args.category

    try:
        data = api_get("/automations", params)
        automations = data if isinstance(data, list) else data.get("automations", [])
    except Exception as e:
        sb = get_supabase()
        if not sb:
            print(f"API error: {e}")
            sys.exit(1)

        query = sb.table("automations").select("*").order("created_at", desc=True)
        if args.type:
            query = query.eq("type", args.type)
        if args.status:
            query = query.eq("status", args.status)
        if args.category:
            query = query.eq("category", args.category)
        automations = query.execute().data

    rows = []
    for a in automations:
        rows.append([
            a.get("slug", "")[:30],
            a.get("type", ""),
            a.get("status", ""),
            a.get("run_count", 0),
            f"{a.get('success_count', 0)}/{a.get('fail_count', 0)}",
            format_timestamp(a.get("last_run_at")),
        ])

    print_table(rows, ["Slug", "Type", "Status", "Runs", "S/F", "Last Run"])


def cmd_automation_detail(args):
    """Get automation details."""
    try:
        auto = api_get(f"/automations/{args.slug}")
    except Exception as e:
        sb = get_supabase()
        if not sb:
            print(f"API error: {e}")
            sys.exit(1)

        result = sb.table("automations").select("*").eq("slug", args.slug).single().execute()
        auto = result.data

    if not auto:
        print(f"Automation '{args.slug}' not found.")
        return

    print(f"\n{'='*60}")
    print(f"AUTOMATION: {auto.get('name')}")
    print(f"{'='*60}")
    print(f"Slug:       {auto.get('slug')}")
    print(f"Type:       {auto.get('type')}")
    print(f"Category:   {auto.get('category') or 'N/A'}")
    print(f"Status:     {auto.get('status')}")
    print(f"Worker:     {auto.get('worker_path') or 'N/A'}")
    print(f"")
    print(f"Run Count:  {auto.get('run_count', 0)}")
    print(f"Successes:  {auto.get('success_count', 0)}")
    print(f"Failures:   {auto.get('fail_count', 0)}")
    print(f"Last Run:   {format_timestamp(auto.get('last_run_at'))}")
    print(f"Last Status:{auto.get('last_run_status') or 'N/A'}")
    print(f"Tags:       {', '.join(auto.get('tags') or [])}")

    if auto.get("description"):
        print(f"\nDescription:\n{auto['description']}")

    if auto.get("config"):
        print(f"\n{'─'*40}")
        print("CONFIG:")
        print(json.dumps(auto["config"], indent=2))


def cmd_stats(args):
    """Show database stats."""
    sb = get_supabase()
    if not sb:
        print("Stats require direct Supabase access. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
        # Try API fallback
        try:
            data = api_get("/stats")
            print(json.dumps(data, indent=2))
            return
        except:
            sys.exit(1)

    # Total logs
    logs_count = sb.table("execution_logs").select("id", count="exact").execute()

    # Logs by status
    success = sb.table("execution_logs").select("id", count="exact").eq("status", "success").execute()
    failed = sb.table("execution_logs").select("id", count="exact").eq("status", "failed").execute()

    # Today's logs
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logs = sb.table("execution_logs").select("id", count="exact").gte("started_at", today.isoformat()).execute()

    # Automations count
    auto_count = sb.table("automations").select("id", count="exact").execute()
    active_auto = sb.table("automations").select("id", count="exact").eq("status", "active").execute()

    print(f"\n{'='*40}")
    print("DATABASE STATS")
    print(f"{'='*40}")
    print(f"Total Logs:         {logs_count.count}")
    print(f"  Successful:       {success.count}")
    print(f"  Failed:           {failed.count}")
    print(f"  Today:            {today_logs.count}")
    print(f"")
    print(f"Automations:        {auto_count.count}")
    print(f"  Active:           {active_auto.count}")


def cmd_failed(args):
    """Show recent failed logs."""
    args.status = "failed"
    args.automation = None
    args.tag = None
    cmd_logs(args)

    # Also show error details for first few
    print("\n" + "="*60)
    print("ERROR DETAILS (first 3):")
    print("="*60)

    try:
        data = api_get("/logs", {"status": "failed", "limit": 3})
        logs = data if isinstance(data, list) else data.get("logs", [])
    except:
        sb = get_supabase()
        if not sb:
            return
        logs = sb.table("execution_logs").select("*").eq("status", "failed").order("started_at", desc=True).limit(3).execute().data

    for log in logs:
        print(f"\n{log.get('id', '')[:8]} - {log.get('automation_slug') or log.get('worker_name', '')}")
        if log.get("error"):
            err = log["error"]
            if isinstance(err, dict):
                print(f"  Error: {err.get('message', err.get('error', str(err)[:200]))}")
            else:
                print(f"  Error: {str(err)[:200]}")


def main():
    parser = argparse.ArgumentParser(description="Query automations database")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # logs command
    logs_parser = subparsers.add_parser("logs", help="List execution logs")
    logs_parser.add_argument("--limit", "-n", type=int, default=20, help="Number of logs")
    logs_parser.add_argument("--status", "-s", help="Filter by status")
    logs_parser.add_argument("--automation", "-a", help="Filter by automation slug")
    logs_parser.add_argument("--tag", "-t", help="Filter by tag")

    # log-detail command
    detail_parser = subparsers.add_parser("log-detail", help="Get full log details")
    detail_parser.add_argument("log_id", help="Log ID (or partial)")

    # automations command
    auto_parser = subparsers.add_parser("automations", help="List automations")
    auto_parser.add_argument("--type", "-t", help="Filter by type")
    auto_parser.add_argument("--status", "-s", help="Filter by status")
    auto_parser.add_argument("--category", "-c", help="Filter by category")

    # automation-detail command
    auto_detail = subparsers.add_parser("automation-detail", help="Get automation details")
    auto_detail.add_argument("slug", help="Automation slug")

    # stats command
    subparsers.add_parser("stats", help="Show database stats")

    # failed command
    failed_parser = subparsers.add_parser("failed", help="Show recent failures")
    failed_parser.add_argument("--limit", "-n", type=int, default=10, help="Number of logs")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "logs": cmd_logs,
        "log-detail": cmd_log_detail,
        "automations": cmd_automations,
        "automation-detail": cmd_automation_detail,
        "stats": cmd_stats,
        "failed": cmd_failed,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
