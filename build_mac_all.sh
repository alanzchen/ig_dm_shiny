rm -rf dist/*.app dist/*.zip && \
./build_arm.sh && ./build_x86.sh && ./codesign.sh