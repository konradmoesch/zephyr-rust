import os
import subprocess
import shutil
import sys
import filecmp

def get_rustc_version():
    result = subprocess.run(['rustc', '-vV'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    for line in lines:
        if line.startswith('release:'):
            return line.split()[1].split('.')[0:2]

def get_host():
    result = subprocess.run(['rustc', '-vV'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    for line in lines:
        if line.startswith('host:'):
            return line.split()[1]

def delete_last_whitespace_if_present(original_string):
    print("original string: " + original_string)
    original_string=str(original_string)
    if (original_string==""):
        return original_string
    print("not empty")
    if (original_string.endswith(' ')):
        print("deleting last whitespace")
        return original_string[:-1]

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
        print(os.path.join(src, 'release', 'deps', '.'))
        print(os.listdir(os.path.join(src, 'release', 'deps', '.')))
        shutil.copytree(os.path.join(src, target, 'release', 'deps'), sysroot_lib_new, dirs_exist_ok=True)
        shutil.copytree(os.path.join(src, 'release', 'deps'), sysroot_lib_host_new, dirs_exist_ok=True)
    print("cp done")

    print(os.listdir(sysroot_lib_host_new))

    diff_result_lib = filecmp.dircmp(sysroot_lib, sysroot_lib_new)
    diff_result_lib_host = filecmp.dircmp(sysroot_lib_host, sysroot_lib_host_new)

    print("diff done")

    if diff_result_lib.diff_files != [] or diff_result_lib_host.diff_files != []:
        shutil.rmtree(clean_dir_if_changed, ignore_errors=True)

    print("start_delete")
    shutil.rmtree(sysroot_lib)
    shutil.rmtree(sysroot_lib_host)
    shutil.move(sysroot_lib_new, sysroot_lib)
    shutil.move(sysroot_lib_host_new, sysroot_lib_host)
    print("delete done")

def build_std(sysroot_build, app_build, sysroot, rust_target_spec, cargo_manifest, rust_target):
    print("Begin build of std")
    cargo_args = ['-v', 'build', f'--target={rust_target_spec}', '--release']
    print(cargo_args)
    rust_flags_step_1 = '-Cembed-bitcode=yes'
    rust_flags_orig = os.environ.get('RUSTFLAGS', '')
    if sys.platform == 'win32':
        rust_flags_orig = delete_last_whitespace_if_present(rust_flags_orig)
        os.environ['RUSTFLAGS'] = rust_flags_orig
    rust_flags = rust_flags_orig + rust_flags_step_1
    print(rust_flags)

    print("running cargo")
    env = os.environ.copy()
    env['RUSTFLAGS'] = rust_flags
    env['RUST_BACKTRACE'] = '1'
    print(sysroot_build + '-stage1')
    subprocess.run(['cargo'] + cargo_args + [ '--target-dir=' + sysroot_build + '-stage1', '--manifest-path=./sysroot-stage1/Cargo.toml', '-p', 'std'], env = env, check=True)
    print("done with cargo")
    host = get_host()
    publish_sysroot(app_build, sysroot, host, rust_target, sysroot_build + '-stage1')

    os.environ['RUSTFLAGS'] = rust_flags_orig + f' --sysroot {sysroot}'
    os.environ['RUST_BACKTRACE'] = '1'
    print(os.environ.get('RUSTFLAGS'))
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
        
        if sys.platform == 'win32':
            sysroot_build = delete_last_whitespace_if_present(sysroot_build)
            os.environ['SYSROOT_BUILD'] = sysroot_build
            app_build = delete_last_whitespace_if_present(app_build)
            os.environ['APP_BUILD'] = app_build
            sysroot = delete_last_whitespace_if_present(sysroot)
            os.environ['SYSROOT'] = sysroot
            rust_target_spec = delete_last_whitespace_if_present(rust_target_spec)
            os.environ['RUST_TARGET_SPEC'] = rust_target_spec
            cargo_manifest = delete_last_whitespace_if_present(cargo_manifest)
            os.environ['CARGO_MANIFEST'] = cargo_manifest
            rust_target = delete_last_whitespace_if_present(rust_target)
            os.environ['RUST_TARGET'] = rust_target

            zephyr_bindgen = delete_last_whitespace_if_present(os.environ.get('ZEPHYR_BINDGEN', ''))
            os.environ['ZEPHYR_BINDGEN'] = zephyr_bindgen
            zephyr_kernel_version_num = delete_last_whitespace_if_present(os.environ.get('ZEPHYR_KERNEL_VERSION_NUM', ''))
            os.environ['ZEPHYR_KERNEL_VERSION_NUM'] = zephyr_kernel_version_num
            config_userspace = delete_last_whitespace_if_present(os.environ.get('CONFIG_USERSPACE', ''))
            os.environ['CONFIG_USERSPACE'] = config_userspace
            config_rust_alloc_pool = delete_last_whitespace_if_present(os.environ.get('CONFIG_RUST_ALLOC_POOL', ''))
            os.environ['CONFIG_RUST_ALLOC_POOL'] = config_rust_alloc_pool
            config_rust_mutex_pool = delete_last_whitespace_if_present(os.environ.get('CONFIG_RUST_MUTEX_POOL', ''))
            os.environ['CONFIG_RUST_MUTEX_POOL'] = config_rust_mutex_pool
            config_posix_clock = delete_last_whitespace_if_present(os.environ.get('CONFIG_POSIX_CLOCK', ''))
            os.environ['CONFIG_POSIX_CLOCK'] = config_posix_clock
            #target_cflags = delete_last_whitespace_if_present(os.environ.get('TARGET_CFLAGS', ''))
            #os.environ['TARGET_CFLAGS'] = target_cflags
            #os.environ['TARGET_CFLAGS'] = "-IC:/ncs/v1.8.0/modules/hal/cmsis/CMSIS/Core/Include -IC:/ncs/v1.8.0/modules/hal/nordic/nrfx -IC:/ncs/v1.8.0/modules/hal/nordic/nrfx/drivers/include -IC:/ncs/v1.8.0/modules/hal/nordic/nrfx/mdk -IC:/ncs/v1.8.0/zephyr/modules/hal_nordic/nrfx/. -IC:/ncs/v1.8.0/modules/debug/segger/SEGGER -IC:/ncs/v1.8.0/modules/debug/segger/Config -IC:/ncs/v1.8.0/zephyr/modules/segger/. -DNRF52832_XXAA " + os.environ['TARGET_CFLAGS']
            os.environ['TARGET_CFLAGS'] = "-IC:/ncs/v1.8.0/zephyr/include -IC:/Develop/helloworld/helloworld_default/build_win/zephyr/include/generated -IC:/ncs/v1.8.0/zephyr/soc/arm/nordic_nrf/nrf52 -IC:/ncs/v1.8.0/zephyr/lib/libc/minimal/include -IC:/ncs/v1.8.0/zephyr/subsys/cpp/include -IC:/ncs/v1.8.0/modules/hal/cmsis/CMSIS/Core/Include -IC:/ncs/v1.8.0/modules/hal/nordic/nrfx -IC:/ncs/v1.8.0/modules/hal/nordic/nrfx/drivers/include -IC:/ncs/v1.8.0/modules/hal/nordic/nrfx/mdk -IC:/ncs/v1.8.0/zephyr/modules/hal_nordic/nrfx/. -IC:/ncs/v1.8.0/modules/debug/segger/SEGGER -IC:/ncs/v1.8.0/modules/debug/segger/Config -IC:/ncs/v1.8.0/zephyr/modules/segger/. -IC:/ncs/v1.8.0/modules/lib/zephyr-rust/uart-buffered/src -DKERNEL -D__ZEPHYR__=1 -D_FORTIFY_SOURCE=2 -DBUILD_VERSION=v2.7.0 -D__PROGRAM_START -DNRF52832_XXAA -DNRF52832_XXAA -imacros C:/Develop/helloworld/helloworld_default/build_win/zephyr/include/generated/autoconf.h --target=thumbv7em-unknown-none-eabi"
            print(f"\"{os.environ['TARGET_CFLAGS']}\"")

        print(f"\"{str(sysroot_build)}\"")
        print(f"\"{str(app_build)}\"")
        print(f"\"{str(sysroot)}\"")
        print(f"\"{str(rust_target_spec)}\"")
        print(f"\"{str(cargo_manifest)}\"")

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
