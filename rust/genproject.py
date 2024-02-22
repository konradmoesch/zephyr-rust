import os
import shutil
import sys

def generate_project(crate_dir, outdir):
    try:
        # Remove existing outdir and create a new one
        shutil.rmtree(outdir, ignore_errors=True)
        os.makedirs(os.path.join(outdir, 'src'), exist_ok=True)

        # Copy Cargo.lock if it exists
        cargo_lock_path = os.path.join(crate_dir, 'Cargo.lock')
        if os.path.exists(cargo_lock_path):
            shutil.copy(cargo_lock_path, outdir)

        # Write to src/lib.rs
        lib_rs_path = os.path.join(outdir, 'src', 'lib.rs')
        with open(lib_rs_path, 'w') as lib_rs_file:
            lib_rs_file.write('extern crate app;\n')

        # Write to Cargo.toml
        cargo_toml_path = os.path.join(outdir, 'Cargo.toml')
        with open(cargo_toml_path, 'w') as cargo_toml_file:
            cargo_toml_file.write(f'''[package]
name = "rust-app"
version = "0.1.0"
edition = "2018"

[lib]
crate-type = ["staticlib"]

[dependencies]
app = {{ path = "{crate_dir}" }}

[profile.release]
panic = "abort"
lto = true
debug = true
opt-level = "s"
''')

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python genproject.py <crate_dir> <outdir>")
        sys.exit(1)

    crate_dir = sys.argv[1]
    outdir = sys.argv[2]

    print(f"Generating project in {outdir}, crate_dir:{crate_dir}")

    generate_project(crate_dir, outdir)
    print("Project generation completed successfully.")
