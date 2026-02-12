
import shutil
import os

def move_project_files():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_project_id = "sFjol5XWRMqEJQMBb2TW"
    target_dir = os.path.join(base_dir, "projects", target_project_id)
    
    # Define source directories/files and their destinations
    moves = {
        "metrics": os.path.join(target_dir, "metrics"),
        "models": os.path.join(target_dir, "models"), 
        "plots": os.path.join(target_dir, "plots")
    }
    
    # Ensure target base exists
    os.makedirs(target_dir, exist_ok=True)
    
    # Move directories
    for src_name, dst_path in moves.items():
        src_path = os.path.join(base_dir, src_name)
        if os.path.exists(src_path):
            if os.path.exists(dst_path):
                shutil.rmtree(dst_path) # Clean target to allow overwrite/move
            print(f"Moving {src_path} -> {dst_path}")
            shutil.move(src_path, dst_path)
        else:
            print(f"Warning: Source {src_path} not found")

    # Move specific file types from directories
    # SUMO files
    sumo_src = os.path.join(base_dir, "sumo")
    sumo_dst = os.path.join(target_dir, "sumo")
    os.makedirs(sumo_dst, exist_ok=True)
    
    if os.path.exists(sumo_src):
        for f in os.listdir(sumo_src):
            if f.endswith(".xml") or f.endswith(".sumocfg"):
                src = os.path.join(sumo_src, f)
                dst = os.path.join(sumo_dst, f)
                print(f"Copying {src} -> {dst}")
                shutil.copy2(src, dst)
    
    # OSM files
    osm_src = os.path.join(base_dir, "osm")
    osm_dst = os.path.join(target_dir, "osm")
    os.makedirs(osm_dst, exist_ok=True)
    
    if os.path.exists(osm_src):
        for f in os.listdir(osm_src):
            if f.endswith(".xml"):
                src = os.path.join(osm_src, f)
                dst = os.path.join(osm_dst, f)
                print(f"Copying {src} -> {dst}")
                shutil.copy2(src, dst)

if __name__ == "__main__":
    move_project_files()
