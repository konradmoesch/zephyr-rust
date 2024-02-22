import os
import subprocess
import shutil
import sys

def get_rustc_version():
    result = subprocess.run(['rustc', '-vV'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    for line in lines:
        if line.startswith('release:'):
            return line.split()[1].split('.')[0:2]

def publish_sysroot(clean_dir_if_changed, sysroot, host, target, *sources):
    print("publish sysroot")

    sysroot_lib = os.path.join(sysroot, 'lib', 'rustlib', target, 'lib')
    sysroot_lib_host = os.path.join(sysroot, 'lib', 'rustlib', host, 'lib')
    sysroot_lib_new = sysroot_lib + '-new'
    sysroot_lib_host_new = sysroot_lib_host + '-new'

    os.makedirs(sysroot_lib, exist_ok=True)
    os.makedirs(sysroot_lib_host, exist_ok=True)
    os.makedirs(sysroot_lib_new, exist_ok=True)
    os.makedirs(sysroot_lib_host_new, exist_ok=True)

    print(sources)

    for src in sources:
        subprocess.run(['cp', '-a', os.path.join(src, target, 'release', 'deps', '.'), sysroot_lib_new], check=True)
        subprocess.run(['cp', '-a', os.path.join(src, 'release', 'deps', '.'), sysroot_lib_host_new], check=True)
    print("cp done")

    diff_result_lib = subprocess.run(['diff', '-qr', sysroot_lib, sysroot_lib_new], capture_output=True, text=True)
    diff_result_lib_host = subprocess.run(['diff', '-qr', sysroot_lib_host, sysroot_lib_host_new], capture_output=True, text=True)

    print(diff_result_lib)
    print("diff done")
    print(diff_result_lib.returncode)
    print(diff_result_lib_host.returncode)

    if diff_result_lib.returncode != 0 or diff_result_lib_host.returncode != 0:
        shutil.rmtree(clean_dir_if_changed, ignore_errors=True)

    print("start_delete")
    shutil.rmtree(sysroot_lib)
    shutil.rmtree(sysroot_lib_host)
    shutil.move(sysroot_lib_new, sysroot_lib)
    shutil.move(sysroot_lib_host_new, sysroot_lib_host)
    print("delete done")

def build_std(sysroot_build, app_build, sysroot, rust_target_spec, cargo_manifest, rust_target):
    print("Begin build of std\n")
    cargo_args = ['-v', 'build', f'--target={rust_target_spec}', '--release']
    print(cargo_args)
    rust_flags_step_1 = '-Cembed-bitcode=yes'
    rust_flags_orig = os.environ.get('RUSTFLAGS', '')
    rust_flags = rust_flags_orig + rust_flags_step_1
    print(rust_flags)

    print("running cargo")
    env = os.environ.copy()
    env['RUSTFLAGS'] = rust_flags
    print(sysroot_build + '-stage1')
    subprocess.run(['/home/km/.cargo/bin/cargo'] + cargo_args + [ '--target-dir=' + sysroot_build + '-stage1', '--manifest-path=./sysroot-stage1/Cargo.toml', '-p', 'std'], env = env, check=True)
    print("done with cargo")
    host = os.environ.get('HOST', '')
    publish_sysroot(app_build, sysroot, host, rust_target, sysroot_build + '-stage1')

    os.environ['RUSTFLAGS'] = rust_flags_orig + f' --sysroot {sysroot}'
    print(os.environ.get('RUSTFLAGS'))
    file = open("/home/km/python_env.txt" , "w")
    file.write(str(os.environ))
    file.close()
    print(os.getcwd())
    subprocess.run(['cargo'] + cargo_args + ['--target-dir=' + app_build, '--manifest-path=' + cargo_manifest], check=True)

if __name__ == "__main__":
    try:
        print("Running buildscript\n")

        sysroot_build = os.environ.get('SYSROOT_BUILD', 'C:/Develop/helloworld/helloworld_default/build/modules/zephyr-rust/sysroot-build')
        app_build = os.environ.get('APP_BUILD', 'C:/Develop/helloworld/helloworld_default/build/modules/zephyr-rust/app')
        sysroot = os.environ.get('SYSROOT', 'C:/Develop/helloworld/helloworld_default/build/modules/zephyr-rust/sysroot')  # Replace with the actual path to sysroot
        rust_target_spec = os.environ.get('RUST_TARGET_SPEC', 'C:/ncs/v1.8.0/modules/lib/zephyr-rust/rust/thumbv7em-none-eabi.json')  # Replace with your target specification
        cargo_manifest = os.environ.get('CARGO_MANIFEST', 'C:/Develop/helloworld/helloworld_default/build/modules/zephyr-rust/rust-app/Cargo.toml')  # Replace with the actual path to Cargo.toml
        rust_target = os.environ.get('RUST_TARGET', '')

        print(sysroot_build)
        print(app_build)
        print(sysroot)
        print(rust_target_spec)
        print(cargo_manifest)

        current_rustc_version = get_rustc_version()
        print("+rustc -vV")
        expected_version = ['1', '68']

        if current_rustc_version != expected_version:
            print(f"Error: Current cargo version: {'.'.join(current_rustc_version)}, expected: {'.'.join(expected_version)}")
            print("If using rustup, it should be automatically installed. If not, run")
            print(f"rustup toolchain install {'.'.join(expected_version)}")
            sys.exit(1)

        # Unstable features are required for building std. Also allow in the app project for now because they're often needed for low level embedded.
        os.environ['RUSTC_BOOTSTRAP'] = '1'

        # Build std
        build_std(sysroot_build, app_build, sysroot, rust_target_spec, cargo_manifest, rust_target)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
