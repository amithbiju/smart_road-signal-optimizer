from flask import Flask, request, jsonify, send_from_directory, abort, Response, stream_with_context
from flask_cors import CORS
import os
import json
import subprocess
import threading
import sys
import pandas as pd
import time
import queue
import xml.etree.ElementTree as ET


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Base directory for all projects
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_ROOT = os.path.join(BASE_DIR, 'projects')

# Global dictionary to store log queues for active projects
# project_id -> queue.Queue
project_logs = {}

def enqueue_output(out, queue):
    """Read lines from stream and add to queue"""
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def run_background_process(command, env, project_id):
    """Run a command in the background and capture output"""
    # Create a queue for this project if it doesn't exist
    if project_id not in project_logs:
        project_logs[project_id] = queue.Queue()
        
    process = subprocess.Popen(
        command, 
        env=env, 
        shell=True, 
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, # Merge stderr into stdout
        bufsize=1, # Line buffered
        text=True # Enable text mode for line buffering
    )
    
    # Start thread to read output
    t = threading.Thread(target=enqueue_output, args=(process.stdout, project_logs[project_id]))
    t.daemon = True
    t.start()
    
    return process

@app.route('/train', methods=['POST'])
def train_model():
    """
    Start a training session for a project.
    Expected JSON body:
    {
        "project_id": "required_string",
        "bbox": {"north": ..., "south": ..., "east": ..., "west": ...}, # optional
        "min_green": 20, # optional
        "episodes": 200, # optional
        "learning_rate": 0.001 # optional
    }
    """
    data = request.json
    if not data or 'project_id' not in data:
        return jsonify({"error": "project_id is required"}), 400
    
    project_id = data['project_id']
    project_path = os.path.join(PROJECTS_ROOT, project_id)
    
    # Prepare environment variables
    env = os.environ.copy()
    env['PROJECT_OUTPUT_DIR'] = project_path
    env['CREATE_DEFAULT_DIRS'] = 'True'
    # Force unbuffered python output for real-time logs
    env['PYTHONUNBUFFERED'] = '1'
    
    # Optional overrides
    if 'bbox' in data:
        env['BOUNDING_BOX'] = json.dumps(data['bbox'])
    if 'min_green' in data:
        env['MIN_GREEN_TIME'] = str(data['min_green'])
    if 'episodes' in data:
        env['MAX_EPISODES'] = str(data['episodes'])
    if 'learning_rate' in data:
        env['LEARNING_RATE'] = str(data['learning_rate'])
        
    # Ensure project directory exists
    os.makedirs(project_path, exist_ok=True)
    
    # Run main.py in background
    cmd = f'"{sys.executable}" main.py'
    
    # Start process with captured output
    threading.Thread(target=run_background_process, args=(cmd, env, project_id)).start()
    
    return jsonify({
        "status": "Training started successfully",
        "project_id": project_id,
        "outputs_location": project_path,
        "message": "View live logs at /logs/" + project_id
    })

@app.route('/logs/<project_id>', methods=['GET'])
def stream_logs(project_id):
    """
    Stream logs for a specific project using Server-Sent Events (SSE).
    """
    def generate():
        if project_id not in project_logs:
            yield "data: Waiting for logs...\n\n"
            return

        q = project_logs[project_id]
        while True:
            try:
                # Non-blocking get
                line = q.get(timeout=1.0)
                # SSE format: "data: <message>\n\n"
                yield f"data: {line}\n\n"
            except queue.Empty:
                # Keep connection alive
                yield ": keep-alive\n\n"
            except Exception:
                break

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/simulate/<project_id>', methods=['POST'])
def run_simulation(project_id):
    """
    Run evaluation/simulation for an existing project.
    """
    project_path = os.path.join(PROJECTS_ROOT, project_id)
    if not os.path.exists(project_path):
        return jsonify({"error": "Project not found"}), 404
    
    env = os.environ.copy()
    env['PROJECT_OUTPUT_DIR'] = project_path
    env['PYTHONUNBUFFERED'] = '1'
    
    # Run evaluate.py
    cmd = f'"{sys.executable}" evaluate.py --mode rl --gui'
    threading.Thread(target=run_background_process, args=(cmd, env, project_id)).start()
    
    return jsonify({"status": "Simulation run started", "project_id": project_id, "message": "View live logs at /logs/" + project_id})

@app.route('/results/<project_id>', methods=['GET'])
def get_results(project_id):
    """Get wait time comparison and other key metrics."""
    project_path = os.path.join(PROJECTS_ROOT, project_id)
    before_file = os.path.join(project_path, 'metrics', 'waiting_time_before.csv')
    after_file = os.path.join(project_path, 'metrics', 'waiting_time_after.csv')
    
    # Check if we have at least one of the files or both
    if not os.path.exists(before_file) and not os.path.exists(after_file):
         return jsonify({"error": "Metrics not found. Has training/evaluation finished?"}), 404
        
    try:
        comparison_data = []
        
        # Calculate comparison if both exist
        if os.path.exists(before_file) and os.path.exists(after_file):
            df_before = pd.read_csv(before_file)
            df_after = pd.read_csv(after_file)
            
            # Handle empty dataframes
            if df_before.empty or df_after.empty:
                avg_before = 0.0
                avg_after = 0.0
                if not df_before.empty:
                     avg_before = df_before['avg_waiting_time'].mean()
                if not df_after.empty:
                     avg_after = df_after['avg_waiting_time'].mean()
            else:
                avg_before = df_before['avg_waiting_time'].mean()
                avg_after = df_after['avg_waiting_time'].mean()

            # Handle NaN values explicitly (e.g. if files exist but have no numeric data)
            if pd.isna(avg_before): avg_before = 0.0
            if pd.isna(avg_after): avg_after = 0.0

            improvement = avg_before - avg_after
            if avg_before != 0:
                improvement_pct = (improvement / avg_before) * 100
            else:
                improvement_pct = 0.0
            
            comparison_data.append({
                "metric": "Average Waiting Time",
                "baseline": round(float(avg_before), 2),
                "rl": round(float(avg_after), 2),
                "improvement": round(float(improvement), 2),
                "improvement_pct": round(float(improvement_pct), 2)
            })
        elif os.path.exists(after_file):
            # Only RL run exists
            df_after = pd.read_csv(after_file)
            if df_after.empty:
                avg_after = 0.0
            else:
                avg_after = df_after['avg_waiting_time'].mean()
            
            if pd.isna(avg_after): avg_after = 0.0

            comparison_data.append({
                "metric": "Average Waiting Time",
                "baseline": None,
                "rl": round(float(avg_after), 2),
                "status": "Baseline not run yet"
            })
            
        queue_file = os.path.join(project_path, 'metrics', 'queue_length_comparison.csv')
        queue_data = []
        if os.path.exists(queue_file):
            queue_df = pd.read_csv(queue_file)
            queue_data = queue_df.to_dict(orient='records')
            
        return jsonify({
            "project_id": project_id,
            "waiting_time_comparison": comparison_data,
            "queue_length_comparison": queue_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/timings/<project_id>', methods=['GET'])
def get_timings(project_id):
    """Get detailed signal phase timings."""
    project_path = os.path.join(PROJECTS_ROOT, project_id)
    timings_file = os.path.join(project_path, 'metrics', 'signal_timings_after.csv')
    
    if not os.path.exists(timings_file):
        return jsonify({"error": "Timing data not found."}), 404
        
    try:
        df = pd.read_csv(timings_file)
        data = df.to_dict(orient='records')[:1000] # Limit to 1000 rows for performance
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/plots/<project_id>/<filename>', methods=['GET'])
def get_plot(project_id, filename):
    """Get generated plot images."""
    project_path = os.path.join(PROJECTS_ROOT, project_id)
    plot_dir = os.path.join(project_path, 'plots')
    return send_from_directory(plot_dir, filename)

@app.route('/status/<project_id>', methods=['GET'])
def get_status(project_id):
    """Check if artifacts exist to guess status."""
    project_path = os.path.join(PROJECTS_ROOT, project_id)
    if not os.path.exists(project_path):
        return jsonify({"status": "Not Found"}), 404
        
    has_model = os.path.exists(os.path.join(project_path, 'models')) and len(os.listdir(os.path.join(project_path, 'models'))) > 0
    has_metrics = os.path.exists(os.path.join(project_path, 'metrics', 'waiting_time_comparison.csv'))
    
    status = "Created"
    if has_model: status = "Training (In Progress or Done)"
    if has_metrics: status = "Completed"
    
    return jsonify({
        "project_id": project_id,
        "status": status,
        "has_models": has_model,
        "has_metrics": has_metrics
    })

def parse_network_phases(net_file):
    """
    Parses the SUMO network XML to build a map of junction_id -> {phase_index: state_string}.
    Returns:
        {
            "junction_id_1": {
                "0": "rrrrGGGGgGGGgg",
                "1": "rrrrGyyyyyyyyy",
                ...
            },
            ...
        }
    """
    if not os.path.exists(net_file):
        return {}
    
    try:
        tree = ET.parse(net_file)
        root = tree.getroot()
        
        junction_phases = {}
        
        for tl_logic in root.findall('tlLogic'):
            junction_id = tl_logic.get('id')
            phases = {}
            for i, phase in enumerate(tl_logic.findall('phase')):
                state = phase.get('state')
                phases[str(i)] = state
            
            junction_phases[junction_id] = phases
            
        return junction_phases
    except Exception as e:
        print(f"Error parsing network XML: {e}")
        return {}

@app.route('/simulation/<project_id>', methods=['GET'])
def get_simulation_data(project_id):
    """
    Returns data for frontend simulation visualization.
    Combines static phase definitions (from net.xml) with dynamic timing logs (from csv).
    """
    project_path = os.path.join(PROJECTS_ROOT, project_id)
    timings_file = os.path.join(project_path, 'metrics', 'signal_timings_after.csv')
    
    # Locate network file (check project dir first, then global sumo dir)
    net_file = os.path.join(project_path, 'sumo', 'network.net.xml')
    if not os.path.exists(net_file):
        net_file = os.path.join(BASE_DIR, 'sumo', 'network.net.xml')
    
    phases_map = parse_network_phases(net_file)
    
    simulation_steps = []
    if os.path.exists(timings_file):
        try:
            df = pd.read_csv(timings_file)
            # We likely only want one episode for simulation, e.g. the last one
            if 'episode' in df.columns and not df.empty:
                last_episode = df['episode'].max()
                df = df[df['episode'] == last_episode]
                simulation_steps = df.to_dict(orient='records')
        except Exception as e:
            return jsonify({"error": f"Error reading timings CSV: {str(e)}"}), 500
            
    return jsonify({
        "project_id": project_id,
        "phase_definitions": phases_map,
        "simulation_log": simulation_steps
    })

if __name__ == '__main__':
    os.makedirs(PROJECTS_ROOT, exist_ok=True)
    print("Starting Traffic Signal Optimization API...")
    print(f"Projects Root: {PROJECTS_ROOT}")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)
