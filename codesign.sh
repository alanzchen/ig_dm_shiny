echo "===== Signing for Intel chip"
codesign -s Developer -v --deep --timestamp --entitlements entitlements.plist -o runtime --force "dist/mac_Intel_chip.app" && \
ditto -c -k --keepParent "dist/mac_Intel_chip.app" dist/mac_Intel_chip_not_stapled.zip && \
xcrun notarytool submit dist/mac_Intel_chip_not_stapled.zip --apple-id me@zenan.ch --password  yhjp-qcbv-yeis-idzr --team-id N9YEGD9WDP --wait && \
xcrun stapler staple "dist/mac_Intel_chip.app" && \
rm dist/mac_Intel_chip_not_stapled.zip && \
ditto -c -k --keepParent "dist/mac_Intel_chip.app" dist/mac_Intel_chip.zip && \
echo "===== Successfully signed for Intel chip"

echo "===== Signing for M chip"
codesign -s Developer -v --deep --timestamp --entitlements entitlements.plist -o runtime --force "dist/mac_M_chip.app" && \
ditto -c -k --keepParent "dist/mac_M_chip.app" dist/mac_M_chip_not_stapled.zip && \
xcrun notarytool submit dist/mac_M_chip_not_stapled.zip --apple-id me@zenan.ch --password  yhjp-qcbv-yeis-idzr --team-id N9YEGD9WDP --wait && \
xcrun stapler staple "dist/mac_M_chip.app" && \
rm dist/mac_M_chip_not_stapled.zip && \
ditto -c -k --keepParent "dist/mac_M_chip.app" dist/mac_M_chip.zip && \
echo "===== Successfully signed for M chip"