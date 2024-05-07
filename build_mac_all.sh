rm -rf dist/*.app && \
./build_arm.sh && ./build_x86.sh && ./codesign.sh