"""
Autonomous Agent Execution Script

Usage:
    python scripts/run_autonomous.py
"""

import sys
import os
import json
from pathlib import Path

# #region agent log
log_path = Path(r"c:\Users\User\ai eng\pet-projects\ai-market-intelligence-agent\.cursor\debug.log")
try:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": "log_path_setup", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:16", "message": "Script started", "data": {"cwd": os.getcwd(), "script_path": __file__, "sys_path": sys.path[:3], "pythonpath": os.environ.get("PYTHONPATH", "not_set")}, "runId": "initial", "hypothesisId": "A"}) + "\n")
except Exception:
    pass
# #endregion

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# #region agent log
try:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": "log_path_added", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:25", "message": "Project root added to path", "data": {"project_root": str(project_root), "sys_path_after": sys.path[:3]}, "runId": "initial", "hypothesisId": "A"}) + "\n")
except Exception:
    pass
# #endregion

# #region agent log
try:
    with open(log_path, "a", encoding="utf-8") as f:
        app_exists = (project_root / "app").exists()
        app_init_exists = (project_root / "app" / "__init__.py").exists()
        f.write(json.dumps({"id": "log_app_check", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:32", "message": "Checking app module structure", "data": {"app_dir_exists": app_exists, "app_init_exists": app_init_exists, "project_root": str(project_root)}, "runId": "initial", "hypothesisId": "C"}) + "\n")
except Exception:
    pass
# #endregion

# Now import app modules (path is set up)
# #region agent log
try:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": "log_before_import", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:47", "message": "About to import app modules", "data": {"sys_path_first": sys.path[0] if sys.path else "empty"}, "runId": "initial", "hypothesisId": "A"}) + "\n")
except Exception as log_err:
    pass
# #endregion

try:
    from app.agents.autonomous_loop import AutonomousLoop
    # #region agent log
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "log_import_1_success", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:54", "message": "Import 1 successful", "data": {"module": "app.agents.autonomous_loop"}, "runId": "initial", "hypothesisId": "A"}) + "\n")
    except Exception:
        pass
    # #endregion
except ImportError as e:
    # #region agent log
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "log_import_1_error", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:61", "message": "Import 1 failed", "data": {"error": str(e), "error_type": type(e).__name__, "sys_path": sys.path[:3]}, "runId": "initial", "hypothesisId": "A"}) + "\n")
    except Exception:
        pass
    # #endregion
    raise

try:
    from app.vector_db.config import VectorDBConfig
    # #region agent log
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "log_import_2_success", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:72", "message": "Import 2 successful", "data": {"module": "app.vector_db.config"}, "runId": "initial", "hypothesisId": "A"}) + "\n")
    except Exception:
        pass
    # #endregion
except ImportError as e:
    # #region agent log
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "log_import_2_error", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:79", "message": "Import 2 failed", "data": {"error": str(e), "error_type": type(e).__name__}, "runId": "initial", "hypothesisId": "A"}) + "\n")
    except Exception:
        pass
    # #endregion
    raise

try:
    from app.config.settings import get_settings
    # #region agent log
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "log_import_3_success", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:90", "message": "Import 3 successful", "data": {"module": "app.config.settings"}, "runId": "initial", "hypothesisId": "A"}) + "\n")
    except Exception:
        pass
    # #endregion
except ImportError as e:
    # #region agent log
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "log_import_3_error", "timestamp": __import__("time").time() * 1000, "location": "run_autonomous.py:97", "message": "Import 3 failed", "data": {"error": str(e), "error_type": type(e).__name__}, "runId": "initial", "hypothesisId": "A"}) + "\n")
    except Exception:
        pass
    # #endregion
    raise

settings = get_settings()


def main():
    """Run the autonomous agent system"""
    
    # Initialize vector DB config
    vector_config = VectorDBConfig(
        persist_directory=settings.vectordb.PERSIST_DIR,
        collection_name=settings.vectordb.COLLECTION_NAME,
        embedding_model=settings.model.EMBEDDING_MODEL,
        batch_size=32,
        max_retries=3
    )
    
    # Create autonomous loop with safety guards
    autonomous_loop = AutonomousLoop(
        vector_db_config=vector_config,
        max_iterations=5,           # Maximum iterations
        score_threshold=0.75,       # Quality threshold to stop
        max_cost=10.0,              # Max cost in dollars (optional)
        max_tokens=50000,           # Max tokens (optional)
        timeout_seconds=300         # 5 minute timeout (optional)
    )
    
    # Define your goal
    goal = "Find underserved SaaS opportunities in AI dev tools"
    
    print("=" * 60)
    print("Autonomous Market Intelligence Agent")
    print("=" * 60)
    print(f"\nGoal: {goal}\n")
    print("Starting autonomous execution...\n")
    
    # Run autonomous loop
    result = autonomous_loop.run(goal=goal)
    
    # Display results
    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(autonomous_loop.get_execution_summary(result))
    
    # Display iteration details
    if result.iterations:
        print("\n" + "=" * 60)
        print("ITERATION DETAILS")
        print("=" * 60)
        for it in result.iterations:
            print(f"\nIteration {it.iteration_number}:")
            print(f"  Execution Time: {it.execution_time:.2f}s")
            if it.critique:
                print(f"  Overall Score: {it.critique.overall_score:.2f}/1.0")
                print(f"  Should Iterate: {it.critique.should_iterate}")
                if it.critique.weaknesses:
                    print(f"  Weaknesses: {', '.join(it.critique.weaknesses[:2])}")
    
    # Display final result
    if result.final_result:
        print("\n" + "=" * 60)
        print("FINAL RESULT")
        print("=" * 60)
        if hasattr(result.final_result, 'summary'):
            print(result.final_result.summary)
        else:
            print(str(result.final_result)[:500])
    
    print("\n" + "=" * 60)
    print(f"✅ Execution completed!")
    print(f"   Total Iterations: {result.total_iterations}")
    print(f"   Total Time: {result.total_execution_time:.2f}s")
    print(f"   Status: {result.status.value}")
    print(f"   Termination: {result.termination_reason}")
    print("=" * 60)


if __name__ == "__main__":
    main()